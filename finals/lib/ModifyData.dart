import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'host_info.dart';

class ModifyDataPage extends StatefulWidget {
  const ModifyDataPage({super.key});

  @override
  State<ModifyDataPage> createState() => _ModifyDataPageState();
}

class _ModifyDataPageState extends State<ModifyDataPage> {
  final Color primaryColor = Color(0xFF5A67D8);
  final _studentIdController = TextEditingController();
  final _gradeController = TextEditingController();
  
  List<dynamic> students = [];
  List<dynamic> semesters = [];
  List<dynamic> subjects = [];
  int? selectedSemesterId;
  int? studentId;
  bool isLoading = false;
  bool hasError = false;
  int limit = 10;
  int page = 1;

  @override
  void initState() {
    super.initState();
    _fetchAllStudents();
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
      final Map<String, String> query = {};
      if (selectedSemesterId != null) {
        query['semester_id'] = selectedSemesterId.toString();
      }

      final uri = Uri.http(apiBaseUrl, '/students/performance/$studentId', query.isNotEmpty ? query : null);
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

  void _showEditGradeDialog(Map<String, dynamic> subject) {
    _gradeController.text = subject['grade'].toString();
    print('Subject data in dialog: $subject'); // Debug log
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

                  setState(() {
                    isLoading = true;
                  });

                  // Debug log the request data
                  final requestData = {
                    'student_id': studentId,
                    'subject_code': subject['subject_code'],
                    'semester_id': selectedSemesterId,
                    'new_grade': newGrade,
                  };
                  print('=== DEBUG LOGS ===');
                  print('Full request data: $requestData');
                  print('Student ID: $studentId (${studentId.runtimeType})');
                  print('Subject code: ${subject['subject_code']} (${subject['subject_code'].runtimeType})');
                  print('Semester ID: $selectedSemesterId (${selectedSemesterId.runtimeType})');
                  print('New grade: $newGrade (${newGrade.runtimeType})');
                  print('API URL: ${Uri.http(apiBaseUrl, '/students/modify/update-grade')}');
                  print('=================');

                  try {
                    final response = await http.post(
                      Uri.http(apiBaseUrl, '/students/modify/update-grade'),
                      headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                      },
                      body: json.encode(requestData),
                    );

                    print('Response status: ${response.statusCode}');
                    print('Response headers: ${response.headers}');
                    print('Response body: ${response.body}');

                    if (response.statusCode == 404) {
                      print('Error: Endpoint not found. Please check if the server is running and the URL is correct.');
                    } else if (response.statusCode == 405) {
                      print('Error: Method not allowed. The server is not accepting POST requests.');
                    } else if (response.statusCode != 200) {
                      print('Error: Server returned status code ${response.statusCode}');
                    }

                    final responseData = json.decode(response.body);

                    if (response.statusCode == 200) {
                      // First show the success message
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('Grade updated successfully'),
                          backgroundColor: Colors.green,
                          duration: Duration(seconds: 2),
                        ),
                      );

                      // Close the dialog
                      Navigator.of(context).pop();

                      // Clear the current data and refresh
                      setState(() {
                        isLoading = true;
                        subjects = []; // Clear current subjects
                      });

                      try {
                        // Add a small delay to ensure backend cache is cleared
                        await Future.delayed(Duration(milliseconds: 100));
                        
                        // Refresh student data with cache-busting parameter
                        final Map<String, String> query = {
                          'semester_id': selectedSemesterId.toString(),
                          'timestamp': DateTime.now().millisecondsSinceEpoch.toString(),
                        };
                        
                        final uri = Uri.http(apiBaseUrl, '/students/performance/$studentId', query);
                        final resp = await http.get(uri);
                        
                        if (resp.statusCode == 200) {
                          final data = json.decode(resp.body);
                          setState(() {
                            subjects = data['subjects'] as List<dynamic>;
                          });
                        }
                        
                        // Refresh all students list with cache-busting
                        final allStudentsQuery = {
                          'page': page.toString(),
                          'limit': limit.toString(),
                          'timestamp': DateTime.now().millisecondsSinceEpoch.toString(),
                        };
                        
                        final allStudentsUri = Uri.http(apiBaseUrl, '/students/performance/all', allStudentsQuery);
                        final allStudentsResp = await http.get(allStudentsUri);
                        
                        if (allStudentsResp.statusCode == 200) {
                          final allStudentsData = json.decode(allStudentsResp.body);
                          setState(() {
                            students = allStudentsData['students'] as List<dynamic>;
                          });
                        }
                      } catch (e) {
                        print('Error refreshing data: $e');
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('Error refreshing data: $e'),
                            backgroundColor: Colors.red,
                          ),
                        );
                      } finally {
                        setState(() {
                          isLoading = false;
                        });
                      }
                    } else {
                      final error = responseData['error'] ?? 'Failed to update grade';
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text(error),
                          backgroundColor: Colors.red,
                        ),
                      );
                    }
                  } catch (e) {
                    print('Error in grade update: $e'); // Debug log
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Error updating grade: $e'),
                        backgroundColor: Colors.red,
                      ),
                    );
                  }
                } catch (e) {
                  print('Error in grade update: $e'); // Debug log
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Error updating grade: $e'),
                      backgroundColor: Colors.red,
                    ),
                  );
                } finally {
                  setState(() {
                    isLoading = false;
                  });
                }
              },
              child: Text('Confirm'),
            ),
          ],
        );
      },
    );
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
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _studentIdController.dispose();
    _gradeController.dispose();
    super.dispose();
  }
}
