using System.IO;
using System.IO.Compression;
using System.Linq;

namespace RandomSongs.Core;

public enum BackupKind
{
    Unknown,
    Full,
    Playlist,
}

public sealed class BackupInfo
{
    public BackupKind Kind { get; init; }
    public int EntryCount { get; init; }
    public string PlaylistId { get; init; } = "";
}

/// <summary>数据备份与恢复：整库打包 / 单歌单打包，以及从备份恢复。</summary>
public static class BackupService
{
    public static string BackupRoot
    {
        get
        {
            var trimmed = AppPaths.DataRoot.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            var parent = Directory.GetParent(trimmed);
            var baseDir = parent?.FullName ?? trimmed;
            return Path.Combine(baseDir, "backups");
        }
    }

    private static string Stamp() => DateTime.Now.ToString("yyyyMMdd_HHmmss");

    /// <summary>在同一秒内多次备份也不会互相覆盖：重名时追加 _2/_3…</summary>
    private static string UniqueArchive(string baseName)
    {
        var path = Path.Combine(BackupRoot, baseName + ".zip");
        var index = 2;
        while (File.Exists(path))
        {
            path = Path.Combine(BackupRoot, $"{baseName}_{index}.zip");
            index++;
        }
        return path;
    }

    private static string Normalize(string entryName) => entryName.Replace('\\', '/');

    private static void AddDirectory(ZipArchive zip, string sourceDir, string entryPrefix)
    {
        foreach (var file in Directory.EnumerateFiles(sourceDir, "*", SearchOption.AllDirectories))
        {
            var rel = Path.GetRelativePath(sourceDir, file).Replace('\\', '/');
            zip.CreateEntryFromFile(file, $"{entryPrefix}/{rel}");
        }
    }

    /// <summary>备份整个 main_data，返回生成的 zip 路径。</summary>
    public static string BackupAll(string suffix = null)
    {
        Directory.CreateDirectory(BackupRoot);
        var baseName = $"main_data_{Stamp()}" + (string.IsNullOrEmpty(suffix) ? "" : $"_{suffix}");
        var archive = UniqueArchive(baseName);
        using var zip = ZipFile.Open(archive, ZipArchiveMode.Create);
        AddDirectory(zip, AppPaths.DataRoot, "main_data");
        return archive;
    }

    /// <summary>备份单个歌单目录，返回生成的 zip 路径。</summary>
    public static string BackupPlaylist(string playlistId)
    {
        var dir = AppPaths.PlaylistDir(playlistId);
        if (!Directory.Exists(dir))
        {
            throw new DirectoryNotFoundException($"歌单目录不存在: {dir}");
        }
        Directory.CreateDirectory(BackupRoot);
        var archive = UniqueArchive($"playlist_{playlistId}_{Stamp()}");
        using var zip = ZipFile.Open(archive, ZipArchiveMode.Create);
        AddDirectory(zip, dir, playlistId);
        return archive;
    }

    /// <summary>识别备份类型：整库（main_data/ 前缀）或单歌单。</summary>
    public static BackupInfo Inspect(string zipPath)
    {
        if (!File.Exists(zipPath))
        {
            throw new FileNotFoundException("备份文件不存在", zipPath);
        }

        using var zip = ZipFile.OpenRead(zipPath);
        var entries = zip.Entries.Where(e => !string.IsNullOrEmpty(e.Name)).ToList();
        if (entries.Any(e => Normalize(e.FullName).StartsWith("main_data/")))
        {
            return new BackupInfo { Kind = BackupKind.Full, EntryCount = entries.Count };
        }

        var topSegments = entries
            .Select(e => Normalize(e.FullName).Split('/'))
            .Where(parts => parts.Length >= 2)
            .Select(parts => parts[0])
            .Distinct()
            .ToList();

        if (topSegments.Count == 1)
        {
            return new BackupInfo
            {
                Kind = BackupKind.Playlist,
                EntryCount = entries.Count,
                PlaylistId = topSegments[0],
            };
        }

        return new BackupInfo { Kind = BackupKind.Unknown, EntryCount = entries.Count };
    }

    /// <summary>
    /// 从整库备份恢复：先做一次安全备份，再用备份内容整体替换 main_data。
    /// 返回安全备份 zip 的路径。
    /// </summary>
    public static string RestoreAll(string zipPath)
    {
        var info = Inspect(zipPath);
        if (info.Kind != BackupKind.Full)
        {
            throw new InvalidOperationException("这不是整库备份（缺少 main_data/ 前缀），无法整体恢复");
        }

        var safety = BackupAll("pre-restore");

        var temp = Path.Combine(Path.GetTempPath(), "rss_restore_" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(temp);
        try
        {
            ZipFile.ExtractToDirectory(zipPath, temp, overwriteFiles: true);
            var extracted = Path.Combine(temp, "main_data");
            if (!Directory.Exists(extracted))
            {
                throw new InvalidOperationException("备份里没有找到 main_data 目录");
            }

            var dataRoot = AppPaths.DataRoot.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            var aside = dataRoot + ".replaced-" + Stamp();

            if (Directory.Exists(dataRoot))
            {
                Directory.Move(dataRoot, aside);
            }
            try
            {
                Directory.Move(extracted, dataRoot);
            }
            catch
            {
                // 回滚
                if (Directory.Exists(dataRoot))
                {
                    Directory.Delete(dataRoot, recursive: true);
                }
                if (Directory.Exists(aside))
                {
                    Directory.Move(aside, dataRoot);
                }
                throw;
            }

            // 安全备份已存在，这里清掉挪开的旧目录
            try
            {
                if (Directory.Exists(aside))
                {
                    Directory.Delete(aside, recursive: true);
                }
            }
            catch
            {
                // 删除失败不影响恢复结果
            }
        }
        finally
        {
            try
            {
                if (Directory.Exists(temp))
                {
                    Directory.Delete(temp, recursive: true);
                }
            }
            catch
            {
                // 忽略
            }
        }

        return safety;
    }

    /// <summary>
    /// 从单歌单备份恢复：解压到目标歌单目录（覆盖），必要时注册歌单。
    /// 返回 (歌单ID, 恢复的文件数)。
    /// </summary>
    public static (string PlaylistId, int Files) RestorePlaylist(string zipPath, string targetPlaylistId = null)
    {
        var info = Inspect(zipPath);
        if (info.Kind != BackupKind.Playlist)
        {
            throw new InvalidOperationException("这不是单歌单备份");
        }

        var playlistId = string.IsNullOrEmpty(targetPlaylistId) ? info.PlaylistId : targetPlaylistId;
        if (string.IsNullOrEmpty(playlistId))
        {
            throw new InvalidOperationException("无法确定歌单 ID");
        }

        if (Directory.Exists(AppPaths.PlaylistDir(playlistId)))
        {
            BackupPlaylist(playlistId); // 覆盖前的安全备份
        }

        var dest = AppPaths.PlaylistDir(playlistId);
        if (Directory.Exists(dest))
        {
            Directory.Delete(dest, recursive: true);
        }
        Directory.CreateDirectory(dest);

        var prefix = info.PlaylistId + "/";
        var count = 0;
        using (var zip = ZipFile.OpenRead(zipPath))
        {
            foreach (var entry in zip.Entries)
            {
                if (string.IsNullOrEmpty(entry.Name))
                {
                    continue; // 目录项
                }
                var name = Normalize(entry.FullName);
                var relative = name.StartsWith(prefix) ? name[prefix.Length..] : name;
                if (relative.Length == 0)
                {
                    continue;
                }
                var outPath = Path.Combine(dest, relative.Replace('/', Path.DirectorySeparatorChar));
                var parent = Path.GetDirectoryName(outPath);
                if (!string.IsNullOrEmpty(parent))
                {
                    Directory.CreateDirectory(parent);
                }
                entry.ExtractToFile(outPath, overwrite: true);
                count++;
            }
        }

        if (ConfigService.GetPlaylist(playlistId) == null)
        {
            PlaylistService.RegisterPlaylist(playlistId, playlistId, "从备份恢复");
        }
        ConfigService.UpdateSongCount(playlistId, SongService.LoadSongs(playlistId).Count);
        return (playlistId, count);
    }
}
