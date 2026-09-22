using System.IO;

namespace RandomSongs.Core;

/// <summary>
/// 统一路径解析。数据根目录决定方式：
///   1. 环境变量 RANDOM_SONGS_DATA
///   2. 可执行文件同级的 main_data（可写时）
///   3. %LOCALAPPDATA%\RandomSongs\main_data
/// 与 Python 版共用同一套 main_data 结构。
/// </summary>
public static class AppPaths
{
    private static string _dataRoot;

    public static string DataRoot
    {
        get => _dataRoot ??= ResolveDefault();
        set => _dataRoot = value;
    }

    private static string ResolveDefault()
    {
        var env = Environment.GetEnvironmentVariable("RANDOM_SONGS_DATA");
        if (!string.IsNullOrWhiteSpace(env))
        {
            return env;
        }

        var beside = Path.Combine(AppContext.BaseDirectory, "main_data");
        try
        {
            Directory.CreateDirectory(beside);
            var probe = Path.Combine(beside, ".write_probe");
            File.WriteAllText(probe, "ok");
            File.Delete(probe);
            return beside;
        }
        catch
        {
            // 落到用户目录
        }

        return Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "RandomSongs",
            "main_data");
    }

    public static string GlobalDir => Path.Combine(DataRoot, "global");
    public static string PlaylistRoot => Path.Combine(DataRoot, "play_list");
    public static string TemplateDir => Path.Combine(DataRoot, "templates");

    public static string GlobalConfigFile => Path.Combine(GlobalDir, "global_config.yaml");
    public static string SystemStatsFile => Path.Combine(GlobalDir, "system_stats.yaml");
    public static string GlobalPlayHistoryFile => Path.Combine(GlobalDir, "global_play_history.log");
    public static string GlobalOperateHistoryFile => Path.Combine(GlobalDir, "global_operate_history.log");

    public static string PlaylistDir(string id) => Path.Combine(PlaylistRoot, id);
    public static string SongsFile(string id) => Path.Combine(PlaylistDir(id), "songs.yaml");
    public static string RequestersFile(string id) => Path.Combine(PlaylistDir(id), "requesters.yaml");
    public static string PlayHistoryFile(string id) => Path.Combine(PlaylistDir(id), "play_history.log");
    public static string OperateHistoryFile(string id) => Path.Combine(PlaylistDir(id), "operate_history.log");
    public static string MusicDir(string id) => Path.Combine(PlaylistDir(id), "music_files");
}
