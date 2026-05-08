import 'dart:async';
import 'dart:io';

/// Starts the PyInstaller-built API server binary that ships next to the Flutter app.
///
/// Per deployment notes, [backend.exe] / [backend] must live in the **same directory**
/// as the Flutter desktop executable (not `Directory.current`, which differs under `flutter run`).
Future<void> startBackend() async {
  try {
    final String exeName = Platform.isWindows ? 'backend.exe' : 'backend';

    final String exeDir = File(Platform.resolvedExecutable).parent.path;
    final String sep = Platform.pathSeparator;
    final String backendPath = '$exeDir$sep$exeName';

    print('[backend_launcher] Flutter executable: ${Platform.resolvedExecutable}');
    print('[backend_launcher] Backend directory: $exeDir');
    print('[backend_launcher] Starting backend at: $backendPath');

    if (!File(backendPath).existsSync()) {
      print('[backend_launcher] ERROR: Backend binary not found.');
      print('[backend_launcher] Expected: $exeName next to the app executable.');
      return;
    }

    await Process.start(
      backendPath,
      <String>[],
      mode: ProcessStartMode.detached,
      workingDirectory: exeDir,
    );

    print('[backend_launcher] Backend process started (detached).');
  } catch (e, st) {
    print('[backend_launcher] Failed to start backend: $e');
    print('[backend_launcher] $st');
  }
}

/// Polls until something accepts TCP on the API port or retries are exhausted.
Future<void> waitForBackend() async {
  const String host = '127.0.0.1';
  const int port = 8765;

  for (int i = 0; i < 10; i++) {
    try {
      final Socket socket = await Socket.connect(
        host,
        port,
        timeout: const Duration(seconds: 1),
      );
      socket.destroy();
      print('[backend_launcher] Backend is ready (attempt ${i + 1}).');
      return;
    } catch (e) {
      print('[backend_launcher] Wait attempt ${i + 1}/10: $e');
      await Future<void>.delayed(const Duration(seconds: 1));
    }
  }

  print('[backend_launcher] Backend not responding, continuing anyway...');
  await Future<void>.delayed(const Duration(seconds: 2));
}
