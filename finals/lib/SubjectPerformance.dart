import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter/services.dart';
import 'host_info.dart';

class StudentPerformancePage extends StatefulWidget {
  @override
  _StudentPerformancePageState createState() => _StudentPerformancePageState();
}

class _StudentPerformancePageState extends State<StudentPerformancePage> {
  List<Map<String, dynamic>> students = [];
  List<Map<String, dynamic>> semesters = [
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
  List<Map<String, dynamic>> subjects = [];

  int? selectedSemesterId;
  int? studentId;
  bool isLoading = false;
  String? errorMessage;

  int currentPage = 1;
  bool hasNextPage = true;

  final TextEditingController _studentIdController = TextEditingController();

  int highlightedIndex = 0;
  late ScrollController _semesterScrollController;

  @override
  void initState() {
    super.initState();
    fetchAllStudents(page: 1);
    _semesterScrollController = ScrollController();
  }

  @override
  void dispose() {
    _semesterScrollController.dispose();
    _studentIdController.dispose();
    super.dispose();
  }

  Future<void> fetchAllStudents({int page = 1}) async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final response = await http.get(
        Uri.parse('http://$apiBaseUrl/students/performance/all?page=$page'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          students = List<Map<String, dynamic>>.from(data['students']);
          currentPage = page;
          hasNextPage = data['has_next'] ?? students.length == 10;
          isLoading = false;
        });
      } else {
        throw Exception('Failed to load students');
      }
    } catch (e) {
      setState(() {
        errorMessage = 'Failed to load students: $e';
        isLoading = false;
      });
    }
  }

  Future<void> fetchStudentSubjects() async {
    if (studentId == null || selectedSemesterId == null) return;

    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final queryParams = {'semester_id': selectedSemesterId.toString()};

      final response = await http.get(
        Uri.http(apiBaseUrl,'/students/performance/$studentId', queryParams),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          subjects = List<Map<String, dynamic>>.from(data['subjects']);
          isLoading = false;
        });
      } else {
        throw Exception('Failed to load subjects');
      }
    } catch (e) {
      setState(() {
        errorMessage = 'Failed to load subjects: $e';
        isLoading = false;
      });
    }
  }

  void _onFetchPressed() {
    final txt = _studentIdController.text.trim();
    setState(() {
      studentId = txt.isEmpty ? null : int.tryParse(txt);
      if (studentId != null) {
        selectedSemesterId = semesters[0]['id'] as int?;
        highlightedIndex = 0;
      } else {
        selectedSemesterId = null;
      }
      subjects = [];
    });

    if (studentId == null) {
      fetchAllStudents(page: 1);
    } else {
      fetchStudentSubjects();
    }
  }

  void _onStudentTap(Map<String, dynamic> student) {
    final id = student['student_id'] as int?;
    if (id != null) {
      _studentIdController.text = id.toString();
      setState(() {
        studentId = id;
        selectedSemesterId = semesters[0]['id'] as int?;
        highlightedIndex = 0;
        subjects = [];
      });
      fetchStudentSubjects();
    }
  }

  @override
  Widget build(BuildContext context) {
    final primaryColor = Theme.of(context).primaryColor;

    return Scaffold(
      appBar: AppBar(title: Text('Student Performance')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _studentIdController,
              decoration: InputDecoration(
                labelText:
                    'Enter Student ID (Leave blank and Fetch to reveal all student list)',
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
            if (studentId == null)
              Expanded(
                child: isLoading
                    ? Center(child: CircularProgressIndicator())
                    : errorMessage != null
                        ? Center(
                            child: Text(
                              errorMessage!,
                              style: TextStyle(color: Colors.red),
                            ),
                          )
                        : Column(
                            children: [
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
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  ElevatedButton(
                                    onPressed: currentPage > 1
                                        ? () => fetchAllStudents(page: currentPage - 1)
                                        : null,
                                    child: Text('Previous'),
                                  ),
                                  Padding(
                                    padding:
                                        const EdgeInsets.symmetric(vertical: 14),
                                    child: Text('Page $currentPage'),
                                  ),
                                  ElevatedButton(
                                    onPressed: hasNextPage
                                        ? () => fetchAllStudents(page: currentPage + 1)
                                        : null,
                                    child: Text('Next'),
                                  ),
                                ],
                              ),
                            ],
                          ),
              )
            else
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    DropdownButtonFormField<int>(
                      value: selectedSemesterId,
                      decoration: InputDecoration(
                        labelText: 'Select School Year and Semester',
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(horizontal: 12),
                      ),
                      isExpanded: true,
                      menuMaxHeight: 160,
                      items: semesters.map((sem) {
                        return DropdownMenuItem<int>(
                          value: sem['id'] as int,
                          child: Text(sem['label']),
                        );
                      }).toList(),
                      onChanged: (int? value) {
                        setState(() {
                          selectedSemesterId = value;
                        });
                        fetchStudentSubjects();
                      },
                    ),
                    SizedBox(height: 12),
                    Expanded(
                      child: isLoading
                          ? Center(child: CircularProgressIndicator())
                          : errorMessage != null
                              ? Center(
                                  child: Text(
                                    errorMessage!,
                                    style: TextStyle(color: Colors.red),
                                  ),
                                )
                              : subjects.isNotEmpty
                                  ? Container(
                                      width: double.infinity,
                                      child: DataTable(
                                        decoration: BoxDecoration(
                                          color: Colors.white,
                                          borderRadius: BorderRadius.circular(12),
                                          boxShadow: [
                                            BoxShadow(
                                                color: Colors.black12,
                                                blurRadius: 6,
                                                offset: Offset(0, 2)),
                                          ],
                                        ),
                                        columns: const [
                                          DataColumn(label: Text('Subject Code')),
                                          DataColumn(label: Text('Student Grade')),
                                          DataColumn(label: Text('Units')),
                                          DataColumn(label: Text('Class Average')),
                                        ],
                                        rows: subjects.map<DataRow>((sub) {
                                          return DataRow(cells: [
                                            DataCell(Text(sub['subject_code'].toString())),
                                            DataCell(Text(sub['grade'].toString())),
                                            DataCell(Text(sub['Units'].toString())),
                                            DataCell(
                                                Text(sub['class_average'].toString())),
                                          ]);
                                        }).toList(),
                                      ),
                                    )
                                  : Center(
                                      child: Text(
                                          'No subjects available for this semester'),
                                    ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
