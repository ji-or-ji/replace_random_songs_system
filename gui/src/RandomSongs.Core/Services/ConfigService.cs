using System.Linq;

namespace RandomSongs.Core;

/// <summary>全局配置与歌单注册表的读写（与 Python 版同一份 global_config.yaml）。</summary>
public static class ConfigService
{
    public static GlobalConfig Load()
    {
        var cfg = YamlStore.Load<GlobalConfig>(AppPaths.GlobalConfigFile) ?? new GlobalConfig();
        cfg.AutoJump ??= new AutoJumpSettings();
        cfg.QqSync ??= new QqSyncSettings();
        cfg.LocalPlayback ??= new LocalPlaybackSettings();
        cfg.Playlists ??= new Dictionary<string, PlaylistEntry>();
        foreach (var entry in cfg.Playlists.Values)
        {
            if (entry == null)
            {
                continue;
            }
            entry.Prevention ??= new DuplicatePrevention();
            entry.Prevention.PlayedSongs ??= new List<PlayedRecord>();
        }
        return cfg;
    }

    public static void Save(GlobalConfig cfg) => YamlStore.Save(AppPaths.GlobalConfigFile, cfg);

    public static bool Exists() => File.Exists(AppPaths.GlobalConfigFile);

    public static string GetCurrentPlaylistId()
    {
        var cfg = Load();
        if (!string.IsNullOrEmpty(cfg.CurrentPlaylist) && cfg.Playlists.ContainsKey(cfg.CurrentPlaylist))
        {
            return cfg.CurrentPlaylist;
        }
        var first = cfg.Playlists.Keys.FirstOrDefault();
        if (first != null)
        {
            cfg.CurrentPlaylist = first;
            Save(cfg);
        }
        return first;
    }

    public static bool SetCurrentPlaylist(string id)
    {
        var cfg = Load();
        if (!cfg.Playlists.ContainsKey(id))
        {
            return false;
        }
        cfg.CurrentPlaylist = id;
        Save(cfg);
        return true;
    }

    public static List<KeyValuePair<string, PlaylistEntry>> GetPlaylists()
        => Load().Playlists.ToList();

    public static PlaylistEntry GetPlaylist(string id)
        => Load().Playlists.TryGetValue(id, out var entry) ? entry : null;

    public static void UpdateSongCount(string id, int count)
    {
        var cfg = Load();
        if (cfg.Playlists.TryGetValue(id, out var entry))
        {
            entry.SongCount = count;
            Save(cfg);
        }
    }

    public static DuplicatePrevention GetPrevention(string id)
    {
        var cfg = Load();
        if (cfg.Playlists.TryGetValue(id, out var entry) && entry.Prevention != null)
        {
            return entry.Prevention;
        }
        return new DuplicatePrevention();
    }

    public static void SavePrevention(string id, DuplicatePrevention prevention)
    {
        var cfg = Load();
        if (cfg.Playlists.TryGetValue(id, out var entry))
        {
            entry.Prevention = prevention;
            Save(cfg);
        }
    }

    public static void SaveAutoJump(AutoJumpSettings autoJump)
    {
        var cfg = Load();
        cfg.AutoJump = autoJump;
        Save(cfg);
    }

    public static LocalPlaybackSettings GetLocalPlayback()
        => Load().LocalPlayback ?? new LocalPlaybackSettings();

    public static void SaveLocalPlayback(LocalPlaybackSettings localPlayback)
    {
        var cfg = Load();
        cfg.LocalPlayback = localPlayback;
        Save(cfg);
    }
}
