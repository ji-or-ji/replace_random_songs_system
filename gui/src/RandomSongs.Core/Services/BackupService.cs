using System.IO;
using System.IO.Compression;

namespace RandomSongs.Core;

/// <summary>数据备份：整库打包，或单个歌单打包。备份放在数据目录同级的 backups/ 下。</summary>
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

    private static void AddDirectory(ZipArchive zip, string sourceDir, string entryPrefix)
    {
        foreach (var file in Directory.EnumerateFiles(sourceDir, "*", SearchOption.AllDirectories))
        {
            var rel = Path.GetRelativePath(sourceDir, file).Replace('\\', '/');
            zip.CreateEntryFromFile(file, $"{entryPrefix}/{rel}");
        }
    }

    /// <summary>备份整个 main_data，返回生成的 zip 路径。</summary>
    public static string BackupAll()
    {
        Directory.CreateDirectory(BackupRoot);
        var archive = Path.Combine(BackupRoot, $"main_data_{Stamp()}.zip");
        if (File.Exists(archive))
        {
            File.Delete(archive);
        }
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
        var archive = Path.Combine(BackupRoot, $"playlist_{playlistId}_{Stamp()}.zip");
        if (File.Exists(archive))
        {
            File.Delete(archive);
        }
        using var zip = ZipFile.Open(archive, ZipArchiveMode.Create);
        AddDirectory(zip, dir, playlistId);
        return archive;
    }
}
