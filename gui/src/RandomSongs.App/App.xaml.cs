using Microsoft.UI.Xaml;

namespace RandomSongs.App;

public partial class App : Application
{
    /// <summary>当前主窗口（供页面拿窗口句柄，例如文件选择器）。</summary>
    public static MainWindow? Instance { get; private set; }

    private Window? _window;

    public App()
    {
        InitializeComponent();
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        _window = new MainWindow();
        Instance = (MainWindow)_window;
        _window.Activate();
    }
}
