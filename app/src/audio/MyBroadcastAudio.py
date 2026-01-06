import flet_audio as fta

class MyBroadcastAudio:
    def __init__(self, src: str):
        self.audio = fta.Audio(src=src)

    async def play(self):
        await self.audio.play()

    async def pause(self):
        await self.audio.pause()

    def set_volume(self, volume: float):
        self.audio.volume = volume

    def set_audio_source(self, src: str):
        self.audio.src = src
        
    def update(self):
        self.audio.update()
