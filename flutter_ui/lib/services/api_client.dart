import 'dart:convert';

import 'package:http/http.dart' as http;

import '../app_constants.dart';

/// HTTP client for ZeroTrace FastAPI backend.
class ApiClient {
  ApiClient({String? baseUrl}) : baseUrl = baseUrl ?? kDefaultApiBaseUrl;

  final String baseUrl;

  Uri _u(String path, [Map<String, String>? query]) {
    final uri = Uri.parse('$baseUrl$path');
    if (query == null || query.isEmpty) return uri;
    return uri.replace(queryParameters: query);
  }

  Future<void> healthCheck() async {
    final r = await http.get(_u('/health'));
    if (r.statusCode != 200) {
      throw ApiException('Backend not reachable (${r.statusCode})');
    }
  }

  Future<List<String>> listDrives() async {
    final r = await http.get(_u('/api/drives'));
    if (r.statusCode != 200) {
      throw ApiException('listDrives failed: ${r.body}');
    }
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    return (j['drives'] as List<dynamic>).cast<String>();
  }

  Future<BrowseResult> browse(String directoryPath) async {
    final r = await http.get(_u('/api/browse', {'path': directoryPath}));
    if (r.statusCode == 403) {
      throw ApiException('Access denied');
    }
    if (r.statusCode != 200) {
      throw ApiException('browse failed: ${r.body}');
    }
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    final entries = (j['entries'] as List<dynamic>)
        .map((e) => BrowseEntry.fromJson(e as Map<String, dynamic>))
        .toList();
    return BrowseResult(
      currentPath: j['current_path'] as String,
      parentPath: j['parent_path'] as String,
      entries: entries,
    );
  }

  Future<int> fileCount(String path) async {
    final r = await http.get(_u('/api/file-count', {'path': path}));
    if (r.statusCode != 200) {
      throw ApiException('file-count failed: ${r.body}');
    }
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    return j['count'] as int;
  }

  Future<int> fileSize(String path) async {
    final r = await http.get(_u('/api/file-size', {'path': path}));
    if (r.statusCode != 200) {
      throw ApiException('file-size failed: ${r.body}');
    }
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    return j['size'] as int;
  }

  /// Mirrors ``os.path.exists`` on the backend (demo / verification).
  Future<bool> pathExists(String path) async {
    final r = await http.get(_u('/api/path-exists', {'path': path}));
    if (r.statusCode != 200) {
      throw ApiException('path-exists failed: ${r.body}');
    }
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    return j['exists'] as bool;
  }

  Future<String> startWipeFile(String path, String method) async {
    return _startWipe('/wipe/file', path, method);
  }

  Future<String> startWipeFolder(String path, String method) async {
    return _startWipe('/wipe/folder', path, method);
  }

  Future<String> startOverwrite(String path, String method) async {
    return _startWipe('/wipe/overwrite', path, method, useHiddenStaging: false);
  }

  Future<String> _startWipe(
    String endpoint,
    String path,
    String method, {
    bool useHiddenStaging = true,
  }) async {
    final r = await http.post(
      _u(endpoint),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'path': path,
        'method': method,
        'use_hidden_staging': useHiddenStaging,
      }),
    );
    if (r.statusCode != 200) {
      throw ApiException('start wipe failed: ${r.body}');
    }
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    return j['job_id'] as String;
  }

  Future<JobStatus> getJob(String jobId) async {
    final r = await http.get(_u('/wipe/jobs/$jobId'));
    if (r.statusCode != 200) {
      throw ApiException('job status failed: ${r.body}');
    }
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    return JobStatus.fromJson(j);
  }
}

class ApiException implements Exception {
  ApiException(this.message);
  final String message;
  @override
  String toString() => message;
}

class BrowseEntry {
  BrowseEntry({
    required this.name,
    required this.path,
    required this.isDirectory,
    required this.isFile,
  });

  final String name;
  final String path;
  final bool isDirectory;
  final bool isFile;

  factory BrowseEntry.fromJson(Map<String, dynamic> j) {
    return BrowseEntry(
      name: j['name'] as String,
      path: j['path'] as String,
      isDirectory: j['is_directory'] as bool,
      isFile: j['is_file'] as bool,
    );
  }
}

class BrowseResult {
  BrowseResult({
    required this.currentPath,
    required this.parentPath,
    required this.entries,
  });

  final String currentPath;
  final String parentPath;
  final List<BrowseEntry> entries;
}

class JobStatus {
  JobStatus({
    required this.jobId,
    required this.status,
    required this.index,
    required this.total,
    required this.currentFile,
    required this.result,
    required this.error,
  });

  final String jobId;
  final String status;
  final int index;
  final int total;
  final String currentFile;
  final Map<String, dynamic>? result;
  final String? error;

  factory JobStatus.fromJson(Map<String, dynamic> j) {
    return JobStatus(
      jobId: j['job_id'] as String,
      status: j['status'] as String,
      index: j['index'] as int? ?? 0,
      total: j['total'] as int? ?? 0,
      currentFile: j['current_file'] as String? ?? '',
      result: j['result'] as Map<String, dynamic>?,
      error: j['error'] as String?,
    );
  }
}
