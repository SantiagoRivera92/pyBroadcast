import os
import threading
import time

try:
    from pydbus import SessionBus
    from pydbus.generic import signal
    from gi.repository import GLib
    HAS_MPRIS_DEPS = True
except ImportError:
    HAS_MPRIS_DEPS = False

class MPRISManager:
    """
    Handles MPRIS (Media Player Remote Interfacing Specification) on Linux.
    Allows the OS and other apps to see what's playing in pyBroadcast.
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.bus = None
        self.loop = None
        self.thread = None
        self.identity = "pyBroadcast"
        self.bus_name = f"org.mpris.MediaPlayer2.pybroadcast"
        
        self._metadata = {}
        self._playback_status = "Stopped"
        self._loop_status = "None"
        self._shuffle = False
        self._volume = 1.0
        self.mpris_object = None
        
    def start(self):
        """Start the MPRIS service in a background thread"""
        if not HAS_MPRIS_DEPS:
            return

        try:
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
        except Exception as e:
            pass

    def _run_loop(self):
        try:
            self.loop = GLib.MainLoop()
            self.bus = SessionBus()
            
            class MediaPlayer2(object):
                """
                <node>
                    <interface name="org.mpris.MediaPlayer2">
                        <property name="CanQuit" type="b" access="read"/>
                        <property name="CanRaise" type="b" access="read"/>
                        <property name="HasTrackList" type="b" access="read"/>
                        <property name="Identity" type="s" access="read"/>
                        <property name="DesktopEntry" type="s" access="read"/>
                        <property name="SupportedUriSchemes" type="as" access="read"/>
                        <property name="SupportedMimeTypes" type="as" access="read"/>
                        <method name="Quit"/>
                        <method name="Raise"/>
                    </interface>
                    <interface name="org.mpris.MediaPlayer2.Player">
                        <property name="PlaybackStatus" type="s" access="read"/>
                        <property name="LoopStatus" type="s" access="readwrite"/>
                        <property name="Volume" type="d" access="readwrite"/>
                        <property name="Shuffle" type="b" access="readwrite"/>
                        <property name="Metadata" type="a{sv}" access="read"/>
                        <property name="Position" type="x" access="read"/>
                        <property name="CanGoNext" type="b" access="read"/>
                        <property name="CanGoPrevious" type="b" access="read"/>
                        <property name="CanPlay" type="b" access="read"/>
                        <property name="CanPause" type="b" access="read"/>
                        <property name="CanSeek" type="b" access="read"/>
                        <method name="Next"/>
                        <method name="Previous"/>
                        <method name="Pause"/>
                        <method name="PlayPause"/>
                        <method name="Stop"/>
                        <method name="Play"/>
                        <method name="Seek">
                            <arg direction="in" name="Offset" type="x"/>
                        </method>
                        <method name="SetPosition">
                            <arg direction="in" name="TrackId" type="o"/>
                            <arg direction="in" name="Position" type="x"/>
                        </method>
                        <method name="OpenUri">
                            <arg direction="in" name="Uri" type="s"/>
                        </method>
                    </interface>
                </node>
                """
                def __init__(self, manager):
                    self.manager = manager
                    
                # Root Interface
                @property
                def CanQuit(self): return True
                @property
                def CanRaise(self): return True
                @property
                def HasTrackList(self): return False
                @property
                def Identity(self): return self.manager.identity
                @property
                def DesktopEntry(self): return "pybroadcast"
                @property
                def SupportedUriSchemes(self): return []
                @property
                def SupportedMimeTypes(self): return []
                def Quit(self): self.manager.main_window.close()
                def Raise(self): pass 
                
                # Player Interface
                @property
                def PlaybackStatus(self): return self.manager._playback_status
                
                @property
                def LoopStatus(self): return self.manager._loop_status
                @LoopStatus.setter
                def LoopStatus(self, value): pass
                    
                @property
                def Volume(self): return self.manager._volume
                @Volume.setter
                def Volume(self, value):
                    self.manager.main_window.set_volume(int(value * 100))
                    
                @property
                def Shuffle(self): return self.manager._shuffle
                @Shuffle.setter
                def Shuffle(self, value): pass
                    
                @property
                def Metadata(self):
                    return self.manager._get_mpris_metadata()
                    
                @property
                def Position(self):
                    return int(self.manager.main_window.media_player.position() * 1000)
                    
                @property
                def CanGoNext(self): return True
                @property
                def CanGoPrevious(self): return True
                @property
                def CanPlay(self): return True
                @property
                def CanPause(self): return True
                @property
                def CanSeek(self): return True
                
                def Next(self): self.manager.main_window.play_next()
                def Previous(self): self.manager.main_window.play_previous()
                def Pause(self): self.manager.main_window.media_player.pause()
                def PlayPause(self): self.manager.main_window.toggle_play()
                def Stop(self): self.manager.main_window.media_player.stop()
                def Play(self): self.manager.main_window.media_player.play()
                def Seek(self, offset): pass
                def SetPosition(self, track_id, position): pass
                def OpenUri(self, uri): pass

            self.mpris_object = MediaPlayer2(self)
            # Standard MPRIS path is /org/mpris/MediaPlayer2
            self.bus.publish(self.bus_name, ("/org/mpris/MediaPlayer2", self.mpris_object))
            self.loop.run()
        except Exception as e:
            pass

    def _get_mpris_metadata(self):
        m = {}
        data = self._metadata
        # D-Bus object path must be valid
        tid = str(data.get('track_id', '0')).replace('-', '_')
        m['mpris:trackid'] = GLib.Variant('o', f"/org/mpris/MediaPlayer2/Track/track_{tid}")
        
        if data.get('title'):
            m['xesam:title'] = GLib.Variant('s', str(data['title']))
        if data.get('artist'):
            m['xesam:artist'] = GLib.Variant('as', [str(data['artist'])])
        if data.get('album'):
            m['xesam:album'] = GLib.Variant('s', str(data['album']))
        if data.get('art_url'):
            m['mpris:artUrl'] = GLib.Variant('s', str(data['art_url']))
        if data.get('length'):
            m['mpris:length'] = GLib.Variant('x', int(float(data['length']) * 1000000))
        return m

    def _emit_properties_changed(self, iface, changed):
        if not self.bus or not self.mpris_object:
            return
        try:
            # params = (interface_name, changed_properties, invalidated_properties)
            params = GLib.Variant("(sa{sv}as)", (iface, changed, []))
            self.bus.con.emit_signal(
                None, # destination
                "/org/mpris/MediaPlayer2",
                "org.freedesktop.DBus.Properties",
                "PropertiesChanged",
                params
            )
        except Exception as e:
            pass
        
    def update_status(self, status):
        """status: 'Playing', 'Paused', 'Stopped'"""
        if self._playback_status == status:
            return
        self._playback_status = status
        self._emit_properties_changed("org.mpris.MediaPlayer2.Player", {"PlaybackStatus": GLib.Variant('s', status)})
        
    def update_metadata(self, track_info):
        self._metadata = track_info
        metadata = self._get_mpris_metadata()
        self._emit_properties_changed("org.mpris.MediaPlayer2.Player", {"Metadata": GLib.Variant('a{sv}', metadata)})
        
    def update_volume(self, volume_float):
        if self._volume == volume_float:
            return
        self._volume = volume_float
        self._emit_properties_changed("org.mpris.MediaPlayer2.Player", {"Volume": GLib.Variant('d', volume_float)})


