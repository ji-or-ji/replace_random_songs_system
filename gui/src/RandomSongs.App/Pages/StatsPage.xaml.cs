using System.Collections.ObjectModel;
using System.Linq;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using RandomSongs.Core;

namespace RandomSongs.App.Pages;

public sealed partial class StatsPage : Page
{
    private readonly ObservableCollection<SimpleTextRow> _requesters = new();
    private readonly ObservableCollection<SongSearchRow> _searchResults = new();
    private readonly ObservableCollection<SimpleTextRow> _history = new();
    private List<Song> _songs = new();
    private string? _playlistId;

    public StatsPage()
    {
        InitializeComponent();
        RequesterList.ItemsSource = _requesters;
        SearchResults.ItemsSource = _searchResults;
        HistoryList.ItemsSource = _history;
        _playlistId = ConfigService.GetCurrentPlaylistId();
        HistoryScopeBox.SelectedIndex = 0;
        Loaded += (_, _) => LoadAll();
    }

    private void LoadAll()
    {
        _playlistId = ConfigService.GetCurrentPlaylistId();
        _songs = string.IsNullOrEmpty(_playlistId) ? new List<Song>() : SongService.LoadSongs(_playlistId);

        var stats = SongService.GetStatistics(_songs);
        TotalsText.Text =
            $"总歌曲数 {stats.TotalSongs} · 有效 {stats.ValidSongs} · 无效 {stats.InvalidSongs} · " +
            $"累计播放 {HistoryService.GetPlayCount()} 次";

        _requesters.Clear();
        if (stats.Requesters.Count == 0)
        {
            _requesters.Add(new SimpleTextRow { Text = "（暂无）" });
        }
        else
        {
            foreach (var kv in stats.Requesters)
            {
                _requesters.Add(new SimpleTextRow { Text = $"{kv.Key}: {kv.Value} 首" });
            }
        }

        RunSearch();
        LoadHistory();
    }

    private void SearchBox_TextChanged(object sender, TextChangedEventArgs e) => RunSearch();

    private void RunSearch()
    {
        var keyword = SearchBox.Text?.Trim() ?? string.Empty;
        _searchResults.Clear();
        IEnumerable<Song> matches = _songs;
        if (keyword.Length > 0)
        {
            matches = _songs.Where(s =>
                (s.SongName ?? "").Contains(keyword, StringComparison.OrdinalIgnoreCase) ||
                (s.Artist ?? "").Contains(keyword, StringComparison.OrdinalIgnoreCase) ||
                (s.RequestedBy ?? "").Contains(keyword, StringComparison.OrdinalIgnoreCase) ||
                (s.Id ?? "").Contains(keyword, StringComparison.OrdinalIgnoreCase));
        }

        var list = matches.ToList();
        foreach (var song in list.Take(500))
        {
            _searchResults.Add(new SongSearchRow
            {
                SongName = song.SongName,
                SubText = $"{song.Artist} · 点歌人 {song.RequestedBy} · {song.Id}",
            });
        }
        SearchInfo.Text = keyword.Length == 0
            ? $"当前歌单 {list.Count} 首（未筛选）"
            : $"匹配 {list.Count} 首";
    }

    private void HistoryScope_Changed(object sender, SelectionChangedEventArgs e) => LoadHistory();

    private void HistoryRefresh_Click(object sender, RoutedEventArgs e) => LoadHistory();

    private void LoadHistory()
    {
        var scope = ParseScope();
        var lines = HistoryService.ReadHistory(scope, _playlistId, limit: 200);
        _history.Clear();
        foreach (var line in lines)
        {
            _history.Add(new SimpleTextRow { Text = line });
        }
        HistoryInfo.Text = lines.Count == 0 ? "暂无记录" : $"最近 {lines.Count} 条（最新在前）";
    }

    private HistoryScope ParseScope()
    {
        var tag = (HistoryScopeBox.SelectedItem as ComboBoxItem)?.Tag as string;
        return tag switch
        {
            "PlaylistOperate" => HistoryScope.PlaylistOperate,
            "GlobalPlay" => HistoryScope.GlobalPlay,
            "GlobalOperate" => HistoryScope.GlobalOperate,
            _ => HistoryScope.PlaylistPlay,
        };
    }
}
