import 'package:flutter/material.dart';

import 'screens/mode_selection_screen.dart';
import 'services/api_client.dart';
import 'services/backend_launcher.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await startBackend();
  await waitForBackend();

  runApp(const ZeroTraceDesktopApp());
}

class ZeroTraceDesktopApp extends StatelessWidget {
  const ZeroTraceDesktopApp({super.key});

  @override
  Widget build(BuildContext context) {
    final api = ApiClient();

    return MaterialApp(
      title: 'ZeroTrace',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: ModeSelectionScreen(api: api),
      builder: (context, child) {
        return MediaQuery(
          data: MediaQuery.of(context).copyWith(textScaler: const TextScaler.linear(1.0)),
          child: child ?? const SizedBox.shrink(),
        );
      },
      debugShowCheckedModeBanner: false,
    );
  }
}
