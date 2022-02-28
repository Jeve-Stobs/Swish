from __future__ import annotations

# stdlib
import asyncio
import base64
import contextlib
import functools
import json
import os
from typing import TYPE_CHECKING, Any

# packages
import yt_dlp


if TYPE_CHECKING:
    # local
    from .app import App


class Search:

    ytdl_options: dict[str, Any] = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/best',
        'restrictfilenames': False,
        'ignoreerrors': True,
        'logtostderr': False,
        'noplaylist': False,
        'nocheckcertificate': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
    }

    def decode_track(self, track: base64) -> dict[str, Any]:
        bytes_ = base64.b64decode(track)
        return json.loads(bytes_.decode())

    def encode_track(self, info: dict[str, Any], *, internal: bool = False) -> base64:
        data = {'id': info['id'], 'title': info['title']}
        if internal:
            data['url'] = info['url']

        jsons = json.dumps(data)
        bytes_ = jsons.encode()

        return base64.b64encode(bytes_).decode()

    async def search_youtube(self, query: str, app: App | None = None, *, raw: bool = False, internal: bool = False):
        self.ytdl_options['source_address'] = app.rotator.rotate() if app else '0.0.0.0'
        YTDL = yt_dlp.YoutubeDL(self.ytdl_options)

        loop = asyncio.get_running_loop()
        partial = functools.partial(YTDL.extract_info, query, download=False)

        with contextlib.redirect_stdout(open(os.devnull, 'w')):
            info = await loop.run_in_executor(None, partial)

        if 'entries' in info:
            if raw:
                tracks = [t for t in info['entries']]
            else:
                tracks = [self.encode_track(t, internal=internal) for t in info['entries']]
        else:
            if raw:
                tracks = [info]
            else:
                tracks = [self.encode_track(info, internal=internal)]

        return tracks
