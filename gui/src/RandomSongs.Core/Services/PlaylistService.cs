using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

namespace RandomSongs.Core;

/// <summary>歌单的创建、注册与数据文件维护。</summary>
public static class PlaylistService
{
    public static string SanitizeId(string name)
    {
        var slug = (name ?? "").Trim().ToLowerInvariant();
        slug = Regex.Replace(slug, @"\s+", "_");
        slug = Regex.Replace(slug, @"[^0-9a-z_\u4e00-\u9fff\-]", "");
        return string.IsNullOrEmpty(slug) ? "playlist" : slug;
    }

    public static string UniquePlaylistId(string name)
    {
        var existing = ConfigService.GetPlaylists().Select(kv => kv.Key).ToHashSet();
        var baseId = SanitizeId(name);
        var candidate = baseId;
        var index = 2;
        while (existing.Contains(candidate))
        {
            candidate = $"{baseId}_{index}";
            index++;
        }
        return candidate;
    }

    /// <summary>新建歌单（注册 + 建数据文件），返回歌单 ID。</summary>
    public static string CreatePlaylist(string name, string description = "")
    {
        var playlistId = UniquePlaylistId(name);
        RegisterPlaylist(playlistId, name, description);
        EnsurePlaylistFiles(playlistId);
        return playlistId;
    }

    /// <summary>创建歌单的数据文件（幂等）。</summary>
    public static string EnsurePlaylistFiles(
        string playlistId,
        IEnumerable<Song> songs = null,
        IEnumerable<Requester> requesters = null)
    {
        Directory.CreateDirectory(AppPaths.PlaylistDir(playlistId));
        Directory.CreateDirectory(AppPaths.MusicDir(playlistId));

        YamlStore.Save(AppPaths.SongsFile(playlistId), new SongFile { Songs = songs?.ToList() ?? new List<Song>() });
        YamlStore.Save(AppPaths.RequestersFile(playlistId), new RequesterFile { Requesters = requesters?.ToList() ?? new List<Requester>() });

        Touch(AppPaths.PlayHistoryFile(playlistId));
        Touch(AppPaths.OperateHistoryFile(playlistId));
        return AppPaths.PlaylistDir(playlistId);
    }

    private static void Touch(string path)
    {
        if (!File.Exists(path))
        {
            File.WriteAllText(path, string.Empty);
        }
    }

    public static PlaylistEntry RegisterPlaylist(string playlistId, string name, string description = "")
    {
        var cfg = ConfigService.Load();
        if (!cfg.Playlists.TryGetValue(playlistId, out var entry) || entry == null)
        {
            entry = new PlaylistEntry();
        }
        entry.Name = name;
        entry.Description = string.IsNullOrEmpty(description)
            ? (string.IsNullOrEmpty(entry.Description) ? $"{name} 歌单" : entry.Description)
            : description;
        entry.CreatedAt ??= DateTime.Now.ToString("yyyy/MM/dd");
        cfg.Playlists[playlistId] = entry;
        ConfigService.Save(cfg);
        return entry;
    }

    public static List<Requester> LoadRequesters(string playlistId)
    {
        var file = YamlStore.Load<RequesterFile>(AppPaths.RequestersFile(playlistId));
        return file?.Requesters ?? new List<Requester>();
    }

    public static bool SaveRequesters(string playlistId, List<Requester> requesters)
    {
        YamlStore.Save(AppPaths.RequestersFile(playlistId), new RequesterFile { Requesters = requesters });
        return true;
    }

    /// <summary>重命名歌单（只改显示名/描述，ID 与目录不变）。</summary>
    public static bool RenamePlaylist(string playlistId, string newName, string newDescription = null)
    {
        var cfg = ConfigService.Load();
        if (!cfg.Playlists.TryGetValue(playlistId, out var entry) || entry == null)
        {
            return false;
        }
        entry.Name = newName;
        if (newDescription != null)
        {
            entry.Description = newDescription;
        }
        ConfigService.Save(cfg);
        return true;
    }

    /// <summary>删除歌单（含数据目录）。不能删最后一个，也不能删当前歌单。</summary>
    public static (bool Ok, string Message) DeletePlaylist(string playlistId)
    {
        var cfg = ConfigService.Load();
        if (!cfg.Playlists.ContainsKey(playlistId))
        {
            return (false, "歌单不存在");
        }
        if (cfg.Playlists.Count <= 1)
        {
            return (false, "至少需要保留一个歌单");
        }
        if (cfg.CurrentPlaylist == playlistId)
        {
            return (false, "不能删除当前正在使用的歌单，请先切换");
        }

        cfg.Playlists.Remove(playlistId);
        ConfigService.Save(cfg);
        try
        {
            Directory.Delete(AppPaths.PlaylistDir(playlistId), recursive: true);
        }
        catch
        {
            // 目录删除失败不影响配置移除
        }
        return (true, "已删除");
    }
}
