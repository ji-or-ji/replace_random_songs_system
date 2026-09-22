using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using RandomSongs.App.Pages;
using RandomSongs.Core;

namespace RandomSongs.App;

public sealed partial class MainWindow : Window
{
    private bool _suppressNav;

    public MainWindow()
    {
        InitializeComponent();
        Title = "随机点歌系统";
        TrySetWindowSize(1100, 740);

        _suppressNav = true;
        Nav.SelectedItem = NavPick;
        _suppressNav = false;
        ContentFrame.Navigate(typeof(PickPage));

        _ = StartupSyncAsync();
    }

    private async Task StartupSyncAsync()
    {
        try
        {
            var message = await QqPlaylistService.AutoSyncOnStartAsync();
            if (!string.IsNullOrEmpty(message))
            {
                ShowStatus(message, InfoBarSeverity.Informational);
            }
        }
        catch
        {
            // 启动同步失败不影响使用
        }
    }

    public void ShowStatus(string message, InfoBarSeverity severity)
    {
        StatusBar.Message = message;
        StatusBar.Severity = severity;
        StatusBar.IsOpen = true;
    }

    private void Nav_SelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs args)
    {
        if (_suppressNav || args.SelectedItem is not NavigationViewItem item)
        {
            return;
        }

        var page = item.Tag?.ToString() switch
        {
            "songs" => typeof(SongsPage),
            "requesters" => typeof(RequestersPage),
            "settings" => typeof(SettingsPage),
            _ => typeof(PickPage),
        };

        if (ContentFrame.CurrentSourcePageType != page)
        {
            ContentFrame.Navigate(page);
        }
    }

    private void TrySetWindowSize(int width, int height)
    {
        try
        {
            var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(this);
            var windowId = Microsoft.UI.Win32Interop.GetWindowIdFromWindow(hwnd);
            var appWindow = Microsoft.UI.Windowing.AppWindow.GetFromWindowId(windowId);
            appWindow.Resize(new Windows.Graphics.SizeInt32(width, height));
        }
        catch
        {
            // 调整窗口大小失败不影响使用
        }
    }
}
