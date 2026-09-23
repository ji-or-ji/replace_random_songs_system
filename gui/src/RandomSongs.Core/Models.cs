using YamlDotNet.Serialization;

namespace RandomSongs.Core;

// 字段名通过 YamlMember 显式指定，保证与 Python 版写出的 YAML 完全兼容。

public sealed class GlobalConfig
{
    [YamlMember(Alias = "system_version")] public string SystemVersion { get; set; } = "2.1";
    [YamlMember(Alias = "initialized_at")] public string InitializedAt { get; set; }
    [YamlMember(Alias = "current_playlist")] public string CurrentPlaylist { get; set; }
    [YamlMember(Alias = "auto_jump")] public AutoJumpSettings AutoJump { get; set; } = new();
    [YamlMember(Alias = "qq_sync")] public QqSyncSettings QqSync { get; set; } = new();
    [YamlMember(Alias = "local_playback")] public LocalPlaybackSettings LocalPlayback { get; set; } = new();
    [YamlMember(Alias = "playlists")] public Dictionary<string, PlaylistEntry> Playlists { get; set; } = new();
}

/// <summary>本地播放模式：启用在“歌曲带本地文件”时直接播放本地文件。</summary>
public sealed class LocalPlaybackSettings
{
    [YamlMember(Alias = "enabled")] public bool Enabled { get; set; }
}

public sealed class AutoJumpSettings
{
    [YamlMember(Alias = "enabled")] public bool Enabled { get; set; }
    [YamlMember(Alias = "mode")] public string Mode { get; set; } = "search"; // search | custom
    [YamlMember(Alias = "custom_url")] public string CustomUrl { get; set; } = "";
    [YamlMember(Alias = "delay")] public int Delay { get; set; } = 3;
    [YamlMember(Alias = "prefer_search")] public bool PreferSearch { get; set; }
}

public sealed class QqSyncSettings
{
    [YamlMember(Alias = "enabled")] public bool Enabled { get; set; } = true;
    [YamlMember(Alias = "playlist_id")] public string PlaylistId { get; set; } = "";
    [YamlMember(Alias = "auto_on_start")] public bool AutoOnStart { get; set; } = true;
}

public sealed class PlaylistEntry
{
    [YamlMember(Alias = "name")] public string Name { get; set; } = "";
    [YamlMember(Alias = "description")] public string Description { get; set; } = "";
    [YamlMember(Alias = "created_at")] public string CreatedAt { get; set; }
    [YamlMember(Alias = "song_count")] public int SongCount { get; set; }
    [YamlMember(Alias = "duplicate_prevention")] public DuplicatePrevention Prevention { get; set; } = new();
}

public sealed class DuplicatePrevention
{
    [YamlMember(Alias = "enabled")] public bool Enabled { get; set; } = true;
    [YamlMember(Alias = "mode")] public string Mode { get; set; } = "time_window"; // time_window | cycle
    [YamlMember(Alias = "time_window_minutes")] public int TimeWindowMinutes { get; set; } = 60;
    [YamlMember(Alias = "reset_on_all_played")] public bool ResetOnAllPlayed { get; set; } = true;
    [YamlMember(Alias = "avoid_immediate_repeat")] public bool AvoidImmediateRepeat { get; set; } = true;
    [YamlMember(Alias = "last_reset_time")] public string LastResetTime { get; set; }
    [YamlMember(Alias = "played_songs")] public List<PlayedRecord> PlayedSongs { get; set; } = new();
}

public sealed class PlayedRecord
{
    [YamlMember(Alias = "song_id")] public string SongId { get; set; } = "";
    [YamlMember(Alias = "song_name")] public string SongName { get; set; } = "";
    [YamlMember(Alias = "play_time")] public string PlayTime { get; set; }
}

public sealed class Song
{
    [YamlMember(Alias = "id")] public string Id { get; set; } = "";
    [YamlMember(Alias = "song_name")] public string SongName { get; set; } = "";
    [YamlMember(Alias = "artist")] public string Artist { get; set; } = "";
    [YamlMember(Alias = "url")] public string Url { get; set; } = "";
    [YamlMember(Alias = "local_path")] public string LocalPath { get; set; } = "";
    [YamlMember(Alias = "requested_by")] public string RequestedBy { get; set; } = "";
    [YamlMember(Alias = "created_at")] public string CreatedAt { get; set; }
    [YamlMember(Alias = "last_modified")] public string LastModified { get; set; }
}

public sealed class SongFile
{
    [YamlMember(Alias = "songs")] public List<Song> Songs { get; set; } = new();
}

public sealed class Requester
{
    [YamlMember(Alias = "name")] public string Name { get; set; } = "";
    [YamlMember(Alias = "email")] public string Email { get; set; } = "";
    [YamlMember(Alias = "notes")] public string Notes { get; set; } = "";
}

public sealed class RequesterFile
{
    [YamlMember(Alias = "requesters")] public List<Requester> Requesters { get; set; } = new();
}

public sealed class SystemStats
{
    [YamlMember(Alias = "total_plays")] public int TotalPlays { get; set; }
    [YamlMember(Alias = "last_play_time")] public string LastPlayTime { get; set; }
}
