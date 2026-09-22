using System.IO;
using System.Text;
using YamlDotNet.Serialization;

namespace RandomSongs.Core;

/// <summary>YAML 读写：原子写入，失败时回退默认值。与 Python 版文件互通。</summary>
public static class YamlStore
{
    private static readonly ISerializer Serializer = new SerializerBuilder()
        .ConfigureDefaultValuesHandling(DefaultValuesHandling.Preserve)
        .Build();

    private static readonly IDeserializer Deserializer = new DeserializerBuilder()
        .IgnoreUnmatchedProperties()
        .Build();

    public static T Load<T>(string path) where T : class
    {
        if (!File.Exists(path))
        {
            return null;
        }

        try
        {
            var text = File.ReadAllText(path, Encoding.UTF8);
            if (string.IsNullOrWhiteSpace(text))
            {
                return null;
            }
            return Deserializer.Deserialize<T>(text);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[警告] 读取 YAML 失败，使用默认值: {path} ({ex.Message})");
            return null;
        }
    }

    public static void Save<T>(string path, T value)
    {
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir))
        {
            Directory.CreateDirectory(dir);
        }

        var text = Serializer.Serialize(value);
        var tmp = path + ".tmp";
        File.WriteAllText(tmp, text, new UTF8Encoding(false));
        File.Move(tmp, path, overwrite: true);
    }

    public static void AppendLine(string path, string line)
    {
        var dir = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir))
        {
            Directory.CreateDirectory(dir);
        }
        File.AppendAllText(path, line.TrimEnd('\n') + Environment.NewLine, new UTF8Encoding(false));
    }

    /// <summary>读取文本文件所有非空行（可选限条数 / 倒序）。</summary>
    public static List<string> ReadLines(string path, int limit = 200, bool newestFirst = false)
    {
        if (string.IsNullOrEmpty(path) || !File.Exists(path))
        {
            return new List<string>();
        }
        try
        {
            var lines = File.ReadAllLines(path, Encoding.UTF8)
                .Where(line => !string.IsNullOrWhiteSpace(line))
                .ToList();
            if (newestFirst)
            {
                lines.Reverse();
            }
            if (limit > 0 && lines.Count > limit)
            {
                lines = lines.Take(limit).ToList();
            }
            return lines;
        }
        catch (IOException)
        {
            return new List<string>();
        }
    }
}
