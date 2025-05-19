import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'host_info.dart';
import 'package:flutter/rendering.dart';

class ModifyDataPage extends StatefulWidget {
  const ModifyDataPage({super.key});

  @override
  State<ModifyDataPage> createState() => _ModifyDataPageState();
}

class _ModifyDataPageState extends State<ModifyDataPage> with AutomaticKeepAliveClientMixin {
  final Color primaryColor = Color(0xFF5A67D8);
  final _studentIdController = TextEditingController();
  final _gradeController = TextEditingController();
  final _emailController = TextEditingController();
  
  List<dynamic> students = [];
  List<dynamic> semesters = [];
  List<dynamic> subjects = [];
  int? selectedSemesterId;
  int? studentId;
  bool isLoading = false;
  bool hasError = false;
  int limit = 10;
  int page = 1;

  // Add new state variables for optimistic updates
  Map<String, dynamic> _pendingUpdates = {};
  bool _isUpdating = false;
  List<Map<String, dynamic>> _batchUpdates = [];

  @override
  bool get wantKeepAlive => false; // This ensures the page refreshes when revisited

  @override
  void initState() {
    super.initState();
    _fetchAllStudents();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Refresh data when page is revisited
    _fetchAllStudents();
  }

  Future<void> _clearCache() async {
    try {
      // Add a small delay to ensure backend cache is cleared
      await Future.delayed(Duration(milliseconds: 100));
      
      // Refresh the current view with cache-busting timestamp
      final timestamp = DateTime.now().millisecondsSinceEpoch.toString();
      
      if (studentId != null) {
        // Refresh student data
        final studentUri = Uri.http(
          apiBaseUrl,
          '/students/performance/$studentId',
          {
            if (selectedSemesterId != null) 'semester_id': selectedSemesterId.toString(),
            'timestamp': timestamp,
          },
        );
        final studentResp = await http.get(
          studentUri,
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
          },
        );
        if (studentResp.statusCode == 200) {
          final studentData = json.decode(studentResp.body);
          setState(() {
            subjects = studentData['subjects'] as List<dynamic>;
          });
        }
      } else {
        // Refresh all students list
        final allStudentsUri = Uri.http(
          apiBaseUrl,
          '/students/performance/all',
          {
            'page': page.toString(),
            'limit': limit.toString(),
            'timestamp': timestamp,
          },
        );
        final allStudentsResp = await http.get(
          allStudentsUri,
          headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
          },
        );
        if (allStudentsResp.statusCode == 200) {
          final allStudentsData = json.decode(allStudentsResp.body);
          setState(() {
            students = allStudentsData['students'] as List<dynamic>;
          });
        }
      }
    } catch (e) {
      print('Error refreshing data: $e');
    }
  }

  Future<void> _fetchAllStudents() async {
    setState(() {
      isLoading = true;
      hasError = false;
    });

    try {
      final Map<String, String> query = {
        'page': page.toString(),
        'limit': limit.toString(),
      };

      final uri = Uri.http(apiBaseUrl, '/students/performance/all', query);
      final resp = await http.get(uri);

      if (resp.statusCode != 200) {
        throw Exception('HTTP ${resp.statusCode}');
      }
      final data = json.decode(resp.body);

      setState(() {
        students = data['students'] as List<dynamic>;
        limit = data['limit'] ?? limit;
        page = data['page'] ?? page;
      });
    } catch (e) {
      print('Error fetching: $e');
      setState(() {
        hasError = true;
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  Future<void> _fetchStudentData() async {
    if (studentId == null) return;

    setState(() {
      isLoading = true;
      hasError = false;
    });

    try {
      final Map<String, String> query = {
        if (selectedSemesterId != null) 'semester_id': selectedSemesterId.toString(),
      };

      final uri = Uri.http(apiBaseUrl, '/students/performance/$studentId', query);
      final resp = await http.get(uri);

      if (resp.statusCode != 200) {
        throw Exception('HTTP ${resp.statusCode}');
      }
      final data = json.decode(resp.body);

      setState(() {
        semesters = [
          {'id': 1, 'label': '2020 - FirstSem'},
          {'id': 2, 'label': '2020 - SecondSem'},
          {'id': 3, 'label': '2020 - Summer'},
          {'id': 4, 'label': '2021 - FirstSem'},
          {'id': 5, 'label': '2021 - SecondSem'},
          {'id': 6, 'label': '2021 - Summer'},
          {'id': 7, 'label': '2022 - FirstSem'},
          {'id': 8, 'label': '2022 - SecondSem'},
          {'id': 9, 'label': '2022 - Summer'},
          {'id': 10, 'label': '2023 - FirstSem'},
          {'id': 11, 'label': '2023 - SecondSem'},
          {'id': 12, 'label': '2023 - Summer'},
          {'id': 13, 'label': '2024 - FirstSem'},
          {'id': 14, 'label': '2024 - SecondSem'},
          {'id': 15, 'label': '2024 - Summer'},
        ];
        subjects = data['subjects'] as List<dynamic>;
        selectedSemesterId = data['semester_id'] as int;
      });
    } catch (e) {
      print('Error fetching: $e');
      setState(() {
        hasError = true;
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  void _onFetchPressed() {
    final txt = _studentIdController.text.trim();
    setState(() {
      studentId = txt.isEmpty ? null : int.tryParse(txt);
      //selectedSemesterId = 1;
      semesters = [];
      subjects = [];
    });
    _fetchStudentData();
  }

  void _onStudentTap(dynamic student) {
    final id = student['student_id'] as int?;
    if (id != null) {
      _studentIdController.text = id.toString();
      setState(() {
        studentId = id;
        selectedSemesterId = 1;
        semesters = [];
        subjects = [];
      });
      _fetchStudentData();
    }
  }

  void _onSemesterChanged(int? semId) {
    setState(() {
      selectedSemesterId = semId;
      subjects = [];
    });
    _fetchStudentData();
  }

  // Add method to handle optimistic updates
  void _optimisticallyUpdateGrade(Map<String, dynamic> subject, double newGrade) {
    final key = '${subject['subject_code']}_${selectedSemesterId}';
    setState(() {
      _pendingUpdates[key] = {
        'original_grade': subject['grade'],
        'new_grade': newGrade,
        'subject': subject,
      };
      
      final subjectIndex = subjects.indexWhere((s) => s['subject_code'] == subject['subject_code']);
      if (subjectIndex != -1) {
        subjects[subjectIndex] = {
          ...subjects[subjectIndex],
          'grade': newGrade,
        };
      }
    });
  }

  // Add method to rollback optimistic updates
  void _rollbackOptimisticUpdate(String key) {
    if (_pendingUpdates.containsKey(key)) {
      final update = _pendingUpdates[key];
      setState(() {
        final subjectIndex = subjects.indexWhere(
          (s) => s['subject_code'] == update['subject']['subject_code']
        );
        if (subjectIndex != -1) {
          subjects[subjectIndex] = {
            ...subjects[subjectIndex],
            'grade': update['original_grade'],
          };
        }
        _pendingUpdates.remove(key);
      });
    }
  }

  // Add method to handle batch updates
  Future<void> _processBatchUpdates() async {
    if (_batchUpdates.isEmpty) return;

    setState(() {
      _isUpdating = true;
    });

    try {
      final response = await http.post(
        Uri.http(apiBaseUrl, '/students/modify/batch-update-grades'),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: json.encode(_batchUpdates),
      );

      final responseData = json.decode(response.body);

      if (response.statusCode == 200) {
        final successfulUpdates = responseData['successful_updates'] as List;
        final errors = responseData['errors'] as List;

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Successfully updated ${successfulUpdates.length} grades. ${errors.length} errors.'),
            duration: Duration(seconds: 3),
          ),
        );

        for (var update in successfulUpdates) {
          for (var subjectCode in update['updated_subjects']) {
            final key = '${subjectCode}_${update['semester_id']}';
            _pendingUpdates.remove(key);
          }
        }

        for (var error in errors) {
          final key = '${error['subject_code']}_${error['semester_id']}';
          _rollbackOptimisticUpdate(key);
        }

        await _fetchStudentData();
        await _fetchAllStudents();
      } else {
        final error = responseData['error'] ?? 'Failed to update grades';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(error),
            backgroundColor: Colors.red,
          ),
        );

        for (var key in _pendingUpdates.keys.toList()) {
          _rollbackOptimisticUpdate(key);
        }
      }
    } catch (e) {
      print('Error in batch update: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to update grades: $e'),
          backgroundColor: Colors.red,
        ),
      );

      for (var key in _pendingUpdates.keys.toList()) {
        _rollbackOptimisticUpdate(key);
      }
    } finally {
      setState(() {
        _isUpdating = false;
        _batchUpdates = [];
      });
    }
  }

  void _showEditGradeDialog(Map<String, dynamic> subject) {
    _gradeController.text = subject['grade'].toString();
    _emailController.text = '';
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Edit Grade'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: Text('${subject['subject_code']}'),
              ),
              SizedBox(height: 16),
              TextField(
                controller: _gradeController,
                decoration: InputDecoration(
                  labelText: 'New Grade',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                onSubmitted: (_) async {
                try {
                  final newGrade = double.tryParse(_gradeController.text);
                  if (newGrade == null || newGrade < 0 || newGrade > 100) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Please enter a valid grade between 0 and 100')),
                    );
                    return;
                  }

                  final email = _emailController.text.trim();
                  if (email.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Email address is required')),
                    );
                    return;
                  }
                  
                  if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(email)) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Please enter a valid email address')),
                    );
                    return;
                  }

                  Navigator.of(context).pop();

                  // Apply optimistic update
                  _optimisticallyUpdateGrade(subject, newGrade);

                  // Add to batch updates
                  _batchUpdates.add({
                    'student_id': studentId,
                    'subject_code': subject['subject_code'],
                    'semester_id': selectedSemesterId,
                    'new_grade': newGrade,
                    'email': email,
                  });

                  // Process batch updates if not already updating
                  if (!_isUpdating) {
                    await _processBatchUpdates();
                  }

                } catch (e) {
                  print('Error in grade update: $e');
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Failed to update grade: $e'),
                      backgroundColor: Colors.red,
                    ),
                  );
                }
              },
              ),
              SizedBox(height: 16),
              TextField(
                controller: _emailController,
                decoration: InputDecoration(
                  labelText: 'Email Address',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.email),
                ),
                keyboardType: TextInputType.emailAddress,
                onSubmitted: (_) async {
                try {
                  final newGrade = double.tryParse(_gradeController.text);
                  if (newGrade == null || newGrade < 0 || newGrade > 100) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Please enter a valid grade between 0 and 100')),
                    );
                    return;
                  }

                  final email = _emailController.text.trim();
                  if (email.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Email address is required')),
                    );
                    return;
                  }
                  
                  if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(email)) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Please enter a valid email address')),
                    );
                    return;
                  }

                  Navigator.of(context).pop();

                  // Apply optimistic update
                  _optimisticallyUpdateGrade(subject, newGrade);

                  // Add to batch updates
                  _batchUpdates.add({
                    'student_id': studentId,
                    'subject_code': subject['subject_code'],
                    'semester_id': selectedSemesterId,
                    'new_grade': newGrade,
                    'email': email,
                  });

                  // Process batch updates if not already updating
                  if (!_isUpdating) {
                    await _processBatchUpdates();
                  }

                } catch (e) {
                  print('Error in grade update: $e');
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Failed to update grade: $e'),
                      backgroundColor: Colors.red,
                    ),
                  );
                }
              },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: Text('Cancel'),
            ),
            ElevatedButton(
              
              onPressed: () async {
                try {
                  final newGrade = double.tryParse(_gradeController.text);
                  if (newGrade == null || newGrade < 0 || newGrade > 100) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Please enter a valid grade between 0 and 100')),
                    );
                    return;
                  }

                  final email = _emailController.text.trim();
                  if (email.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Email address is required')),
                    );
                    return;
                  }
                  
                  if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(email)) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Please enter a valid email address')),
                    );
                    return;
                  }

                  Navigator.of(context).pop();

                  // Apply optimistic update
                  _optimisticallyUpdateGrade(subject, newGrade);

                  // Add to batch updates
                  _batchUpdates.add({
                    'student_id': studentId,
                    'subject_code': subject['subject_code'],
                    'semester_id': selectedSemesterId,
                    'new_grade': newGrade,
                    'email': email,
                  });

                  // Process batch updates if not already updating
                  if (!_isUpdating) {
                    await _processBatchUpdates();
                  }

                } catch (e) {
                  print('Error in grade update: $e');
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Failed to update grade: $e'),
                      backgroundColor: Colors.red,
                    ),
                  );
                }
              },
              child: Text('Update'),
            ),
          ],
        );
      },
    );
  }

  // Add a method to show batch update status
  Widget _buildBatchUpdateStatus() {
    if (_isUpdating) {
      return Padding(
        padding: const EdgeInsets.all(8.0),
        child: Row(
          children: [
            SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: 8),
            Text('Updating grades...'),
          ],
        ),
      );
    }
    return SizedBox.shrink();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Modify Grade')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Student ID input field and fetch button
            TextField(
              controller: _studentIdController,
              decoration: InputDecoration(
                labelText: 'Enter Student ID (or leave blank to show all students)',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.person),
              ),
              keyboardType: TextInputType.number,
              onSubmitted: (_) => _onFetchPressed(),
            ),
            SizedBox(height: 8),
            ElevatedButton(
              onPressed: _onFetchPressed,
              child: Text('Fetch Data'),
            ),
            SizedBox(height: 16),

            if (isLoading) ...[
              Center(child: CircularProgressIndicator()),
            ] else if (hasError) ...[
              Center(child: Text('Failed to load data.')),
            ] else ...[
              if (studentId == null) ...[
                // Show list of students
                Expanded(
                  child: ListView.builder(
                    itemCount: students.length,
                    itemBuilder: (_, i) {
                      final s = students[i];
                      return Card(
                        margin: EdgeInsets.symmetric(vertical: 6),
                        child: ListTile(
                          title: Text(s['name']),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('GPA: ${s['overall_gpa']}'),
                              Text('Weighted Avg: ${s['weighted_average']}'),
                            ],
                          ),
                          onTap: () => _onStudentTap(s),
                        ),
                      );
                    },
                  ),
                ),
                // Pagination buttons
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8.0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      ElevatedButton(
                        onPressed: page > 1
                            ? () {
                                setState(() => page--);
                                _fetchAllStudents();
                              }
                            : null,
                        child: Text('Prev Page'),
                      ),
                      Text('Page $page', style: TextStyle(fontSize: 12)),
                      ElevatedButton(
                        onPressed: students.length == limit
                            ? () {
                                setState(() => page++);
                                _fetchAllStudents();
                              }
                            : null,
                        child: Text('Next Page'),
                      ),
                    ],
                  ),
                ),
              ] else ...[
                // Show student's grades
                if (semesters.isNotEmpty) ...[
                  DropdownButtonFormField<int>(
                    menuMaxHeight: 160,
                    value: selectedSemesterId,
                    decoration: InputDecoration(
                      labelText: 'Select Semester',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.calendar_month_rounded),
                    ),
                    items: semesters.map<DropdownMenuItem<int>>((sem) {
                      return DropdownMenuItem<int>(
                        value: sem['id'],
                        child: Text(sem['label']),
                      );
                    }).toList(),
                    onChanged: _onSemesterChanged,
                  ),
                  SizedBox(height: 12),
                ],

                if (subjects.isNotEmpty) ...[
                  Expanded(
                    child: Container(
                      width: double.infinity,
                      child: DataTable(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                          boxShadow: [
                            BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2))
                          ],
                        ),
                        columns: const [
                          DataColumn(label: Text('Subject Code')),
                          DataColumn(label: Text('Student Grade')),
                          DataColumn(label: Text('Actions')),
                        ],
                        rows: subjects.map<DataRow>((sub) {
                          return DataRow(cells: [
                            DataCell(Text(sub['subject_code'].toString())),
                            DataCell(Text(sub['grade'].toString())),
                            DataCell(
                              IconButton(
                                icon: Icon(Icons.edit, color: primaryColor),
                                onPressed: () => _showEditGradeDialog(sub),
                              ),
                            ),
                          ]);
                        }).toList(),
                      ),
                    ),
                  ),
                ],
              ],
            ],
            _buildBatchUpdateStatus(),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _clearCache();
    _studentIdController.dispose();
    _gradeController.dispose();
    _emailController.dispose();
    super.dispose();
  }
}


