import 'dart:async';

import 'package:flutter/material.dart';

import '../models/app_mode.dart';
import '../services/api_client.dart';
import 'result_screen.dart';

/// Step 6 — shows wipe progress (maps to per-file loop in ``main.py``).
class ProgressScreen extends StatefulWidget {
  const ProgressScreen({
    super.key,
    required this.api,
    required this.mode,
    required this.targetPath,
    required this.targetIsFile,
    required this.nistMethod,
  });

  final ApiClient api;
  final AppMode mode;
  final String targetPath;
  final bool targetIsFile;
  final String nistMethod;

  @override
  State<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends State<ProgressScreen> {
  Timer? _timer;
  String? _jobId;
  JobStatus? _status;
  String? _startError;
  bool _navigated = false;

  @override
  void initState() {
    super.initState();
    _start();
  }

  Future<void> _start() async {
    try {
      final id = await _startJob();
      if (!mounted) return;
      setState(() {
        _jobId = id;
      });
      _timer = Timer.periodic(const Duration(milliseconds: 350), (_) async {
        if (_jobId == null) return;
        try {
          final s = await widget.api.getJob(_jobId!);
          if (!mounted) return;
          setState(() => _status = s);
          if ((s.status == 'completed' || s.status == 'failed') && !_navigated) {
            _navigated = true;
            _timer?.cancel();
            _timer = null;
            if (!mounted) return;
            final r = s.result;
            final ok = r != null && (r['success'] == true);
            await Navigator.of(context).pushReplacement(
              MaterialPageRoute<void>(
                builder: (_) => ResultScreen(
                  api: widget.api,
                  jobStatus: s,
                  success: ok,
                  originalTargetPath: widget.targetPath,
                ),
              ),
            );
          }
        } catch (e) {
          if (_navigated) return;
          _navigated = true;
          _timer?.cancel();
          _timer = null;
          if (!mounted) return;
          await Navigator.of(context).pushReplacement(
            MaterialPageRoute<void>(
              builder: (_) => ResultScreen(
                api: widget.api,
                jobStatus: null,
                success: false,
                originalTargetPath: widget.targetPath,
                errorText: e.toString(),
              ),
            ),
          );
        }
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _startError = e.toString());
    }
  }

  Future<String> _startJob() async {
    if (widget.mode == AppMode.overwriteOnly) {
      return widget.api.startOverwrite(widget.targetPath, widget.nistMethod);
    }
    if (widget.targetIsFile) {
      return widget.api.startWipeFile(widget.targetPath, widget.nistMethod);
    }
    return widget.api.startWipeFolder(widget.targetPath, widget.nistMethod);
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_startError != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Progress')),
        body: Center(child: Text(_startError!)),
      );
    }

    final total = _status?.total ?? 0;
    final idx = _status?.index ?? 0;
    final op = _status?.currentFile ?? '';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Secure wipe in progress'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              widget.mode == AppMode.overwriteOnly
                  ? 'Overwrite operation'
                  : 'Wiping files…',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            if (total > 0)
              LinearProgressIndicator(value: (idx.clamp(0, total)) / total)
            else
              const LinearProgressIndicator(),
            const SizedBox(height: 16),
            Text('Current operation:\n$op', style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 8),
            Text(
              'Job: ${_jobId ?? "starting…"}  |  Status: ${_status?.status ?? "queued"}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}
