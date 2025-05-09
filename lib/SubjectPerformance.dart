import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'host_info.dart';

class StudentPerformancePage extends StatefulWidget {
  @override
  _StudentPerformancePageState createState() => _StudentPerformancePageState();
}

class _StudentPerformancePageState extends State<StudentPerformancePage> {
  // "All"‑view data
  List<dynamic> students = [];
  int limit = 10, page = 1;

  // Single‑student performance data
  List<dynamic> semesters = [];
  List<dynamic> subjects = [];

  int? selectedSemesterId;
  int? studentId;

  bool isLoading = false;
  bool hasError = false;

  final TextEditingController _studentIdController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchAllOrOne();
  }

  Future<void> _fetchAllOrOne() async {
    setState(() {
      isLoading = true;
      hasError = false;
    });

    try {
      final bool allView = (studentId == null);
      final path = allView
          ? '/students/performance/all'
          : '/students/performance/$studentId';

      // Build query params
      final Map<String, String> query = {};
      if (allView) {
        query['page'] = page.toString();
        query['limit'] = limit.toString();
      } else if (selectedSemesterId != null) {
        query['semester_id'] = selectedSemesterId.toString();
      }

      final uri = Uri.http(apiBaseUrl, path, query.isNotEmpty ? query : null);
      final resp = await http.get(uri);

      if (resp.statusCode != 200) {
        throw Exception('HTTP ${resp.statusCode}');
      }
      final data = json.decode(resp.body);

      setState(() {
        if (allView) {
          students = data['students'] as List<dynamic>;
          limit = data['limit'] ?? limit;
          page = data['page'] ?? page;
          semesters = [];
          subjects = [];
        } else {
          semesters = data['semesters'] as List<dynamic>;
          subjects = data['performance']['subjects'] as List<dynamic>;
          students = [];
        }
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
      selectedSemesterId = null;
      students = [];
      semesters = [];
      subjects = [];
      page = 1; // reset to first page on new fetch
    });
    _fetchAllOrOne();
  }

  void _onSemesterChanged(int? semId) {
    setState(() {
      selectedSemesterId = semId;
      subjects = [];
    });
    _fetchAllOrOne();
  }

  void _onStudentTap(dynamic student) {
    final id = student['student_id'] as int?;
    if (id != null) {
      _studentIdController.text = id.toString();
      setState(() {
        studentId = id;
        selectedSemesterId = null;
        students = [];
        semesters = [];
        subjects = [];
      });
      _fetchAllOrOne();
    }
  }

  @override
  void dispose() {
    _studentIdController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Student Performance')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _studentIdController,
              decoration: InputDecoration(
                labelText: 'Enter Student ID (Leave blank and Fetch to reveal all student list)',
                border: OutlineInputBorder(),
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
              // "All" view
              if (studentId == null && students.isNotEmpty) ...[
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
                                _fetchAllOrOne();
                              }
                            : null,
                        child: Text('Prev Page'),
                      ),
                      Text('Page $page', style: TextStyle(fontSize: 12)),
                      ElevatedButton(
                        onPressed: students.length == limit
                            ? () {
                                setState(() => page++);
                                _fetchAllOrOne();
                              }
                            : null,
                        child: Text('Next Page'),
                      ),
                    ],
                  ),
                ),
              ],

              // Single‑student view
              if (studentId != null && semesters.isNotEmpty) ...[
                DropdownButtonFormField<int>(
                  value: selectedSemesterId,
                  decoration: InputDecoration(
                    labelText: 'Select Semester',
                    border: OutlineInputBorder(),
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

              if (studentId != null && subjects.isNotEmpty) ...[
                Expanded(
                  child: Container(
                    //scrollDirection: Axis.horizontal,
                    width:double.infinity,
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
                        DataColumn(label: Text('Units')),
                        DataColumn(label: Text('Class Average')),
                      ],
                      
                      rows: subjects.map<DataRow>((sub) {
                        return DataRow(cells: [
                          DataCell(Text(sub['subject_code'].toString())),
                          DataCell(Text(sub['grade'].toString())),
                          DataCell(Text(sub['Units'].toString())),
                          DataCell(Text(sub['class_average'].toString())),
                        ]);
                      }).toList(),
                    ),
                  ),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }
}
