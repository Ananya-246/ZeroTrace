import 'package:flutter/material.dart';

import '../models/app_mode.dart';
import '../services/api_client.dart';
import 'wipe_method_screen.dart';

/// Mode 3 — mirrors ``main.py`` lines showing selected file and size before method.
class OverwriteSummaryScreen extends StatefulWidget {
  const OverwriteSummaryScreen({
    super.key,
    required this.api,
    required this.filePath,
  });

  final ApiClient api;
  final String filePath;

  @override
  State<OverwriteSummaryScreen> createState() => _OverwriteSummaryScreenState();
}

class _OverwriteSummaryScreenState extends State<OverwriteSummaryScreen> {
  late Future<int> _sizeFuture;

  @override
  void initState() {
    super.initState();
    _sizeFuture = widget.api.fileSize(widget.filePath);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Overwrite Only'),
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: FutureBuilder<int>(
              future: _sizeFuture,
              builder: (context, snap) {
                if (snap.connectionState != ConnectionState.done) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snap.hasError) {
                  return Text('Error: ${snap.error}');
                }
                final bytes = snap.data ?? 0;
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text('Selected:', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    SelectableText(widget.filePath),
                    const SizedBox(height: 16),
                    Text('Size    : $bytes bytes'),
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute<void>(
                            builder: (_) => WipeMethodScreen(
                              api: widget.api,
                              mode: AppMode.overwriteOnly,
                              targetPath: widget.filePath,
                              targetIsFile: true,
                              isOverwrite: true,
                            ),
                          ),
                        );
                      },
                      child: const Text('Continue to overwrite method'),
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('Cancel'),
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}
