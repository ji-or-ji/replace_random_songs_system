using System.Collections.ObjectModel;
using System.Linq;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using RandomSongs.Core;

namespace RandomSongs.App.Pages;

public sealed class RequesterRow
{
    public string Name { get; set; } = "";
    public int Count { get; set; }
    public string CountText => $"{Count} 首";
}

public sealed partial class RequestersPage : Page
{
    private readonly ObservableCollection<RequesterRow> _rows = new();
    private string? _playlistId;

    public RequestersPage()
    {
        InitializeComponent();
        RequesterList.ItemsSource = _rows;
        Loaded += (_, _) => Load();
    }

    private void Load()
    {
        _playlistId = ConfigService.GetCurrentPlaylistId();
        _rows.Clear();
        if (!string.IsNullOrEmpty(_playlistId))
        {
            var requesters = PlaylistService.LoadRequesters(_playlistId);
            var counts = SongService.LoadSongs(_playlistId)
                .GroupBy(s => string.IsNullOrEmpty(s.RequestedBy) ? "未知" : s.RequestedBy)
                .ToDictionary(g => g.Key, g => g.Count());
            foreach (var requester in requesters)
            {
                _rows.Add(new RequesterRow
                {
                    Name = requester.Name,
                    Count = counts.TryGetValue(requester.Name, out var c) ? c : 0,
                });
            }
        }
        var name = string.IsNullOrEmpty(_playlistId) ? "-" : ConfigService.GetPlaylist(_playlistId)?.Name ?? _playlistId;
        HeaderText.Text = $"点歌人管理 · {name}（{_rows.Count} 位）";
    }

    private void Refresh_Click(object sender, RoutedEventArgs e) => Load();

    private async void Add_Click(object sender, RoutedEventArgs e)
    {
        if (string.IsNullOrEmpty(_playlistId))
        {
            return;
        }
        var box = new TextBox { Header = "点歌人姓名", Width = 320 };
        var dialog = new ContentDialog
        {
            Title = "添加点歌人",
            Content = box,
            PrimaryButtonText = "添加",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Primary,
            XamlRoot = XamlRoot,
            IsPrimaryButtonEnabled = false,
        };
        box.TextChanged += (_, _) => dialog.IsPrimaryButtonEnabled = !string.IsNullOrWhiteSpace(box.Text);
        if (await dialog.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }

        var name = box.Text.Trim();
        var requesters = PlaylistService.LoadRequesters(_playlistId);
        if (requesters.Any(r => r.Name == name))
        {
            await ShowMessage($"点歌人「{name}」已存在");
            return;
        }
        requesters.Add(new Requester { Name = name });
        PlaylistService.SaveRequesters(_playlistId, requesters);
        HistoryService.RecordOperation("添加点歌人", $"点歌人: {name}", playlistId: _playlistId);
        Load();
    }

    private async void Rename_Click(object sender, RoutedEventArgs e)
    {
        if (RequesterList.SelectedItem is not RequesterRow row || string.IsNullOrEmpty(_playlistId))
        {
            await ShowMessage("请先选择一位点歌人");
            return;
        }

        var box = new TextBox { Header = "新的姓名", Text = row.Name, Width = 320 };
        var dialog = new ContentDialog
        {
            Title = "重命名点歌人",
            Content = box,
            PrimaryButtonText = "保存",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Primary,
            XamlRoot = XamlRoot,
        };
        if (await dialog.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }

        var newName = box.Text.Trim();
        if (string.IsNullOrEmpty(newName) || newName == row.Name)
        {
            return;
        }

        var requesters = PlaylistService.LoadRequesters(_playlistId);
        if (requesters.Any(r => r.Name == newName))
        {
            await ShowMessage($"点歌人「{newName}」已存在");
            return;
        }

        var target = requesters.First(r => r.Name == row.Name);
        target.Name = newName;
        PlaylistService.SaveRequesters(_playlistId, requesters);

        var songs = SongService.LoadSongs(_playlistId);
        var changed = 0;
        foreach (var song in songs.Where(s => s.RequestedBy == row.Name))
        {
            song.RequestedBy = newName;
            changed++;
        }
        if (changed > 0)
        {
            SongService.SaveSongs(_playlistId, songs);
        }

        HistoryService.RecordOperation(
            "修改点歌人",
            $"原姓名: {row.Name} -> 新姓名: {newName}（同步 {changed} 首歌）",
            playlistId: _playlistId);
        Load();
    }

    private async void Delete_Click(object sender, RoutedEventArgs e)
    {
        if (RequesterList.SelectedItem is not RequesterRow row || string.IsNullOrEmpty(_playlistId))
        {
            await ShowMessage("请先选择一位点歌人");
            return;
        }

        var confirm = new ContentDialog
        {
            Title = "删除点歌人",
            Content = $"确定删除「{row.Name}」吗？（不会改动已有歌曲的点歌人字段）",
            PrimaryButtonText = "删除",
            CloseButtonText = "取消",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = XamlRoot,
        };
        if (await confirm.ShowAsync() != ContentDialogResult.Primary)
        {
            return;
        }

        var requesters = PlaylistService.LoadRequesters(_playlistId);
        requesters.RemoveAll(r => r.Name == row.Name);
        PlaylistService.SaveRequesters(_playlistId, requesters);
        HistoryService.RecordOperation("删除点歌人", $"点歌人: {row.Name}", playlistId: _playlistId);
        Load();
    }

    private async Task ShowMessage(string message)
    {
        var dialog = new ContentDialog
        {
            Title = "提示",
            Content = message,
            CloseButtonText = "好",
            XamlRoot = XamlRoot,
        };
        await dialog.ShowAsync();
    }
}
