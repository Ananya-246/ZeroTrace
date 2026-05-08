/// Mirrors ``main.py`` mode choices (1 / 2 / 3).
enum AppMode {
  /// Mode 1 — Wipe User Data (Navigate & Delete)
  wipeUserData,

  /// Mode 2 — Wipe Entire Drive
  wipeEntireDrive,

  /// Mode 3 — Overwrite Only (Keep File, Wipe Content)
  overwriteOnly,
}

extension AppModeLabels on AppMode {
  String get title {
    switch (this) {
      case AppMode.wipeUserData:
        return 'Wipe User Data';
      case AppMode.wipeEntireDrive:
        return 'Wipe Entire Drive';
      case AppMode.overwriteOnly:
        return 'Overwrite Only';
    }
  }

  int get cliNumber {
    switch (this) {
      case AppMode.wipeUserData:
        return 1;
      case AppMode.wipeEntireDrive:
        return 2;
      case AppMode.overwriteOnly:
        return 3;
    }
  }
}
