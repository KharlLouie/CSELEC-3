import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'host_info.dart';
import 'package:flutter/rendering.dart';

class StudentRiskAnalyticsPage extends StatefulWidget {
  @override
  _StudentRiskAnalyticsPageState createState() =>
      _StudentRiskAnalyticsPageState();
}

class _StudentRiskAnalyticsPageState extends State<StudentRiskAnalyticsPage> with AutomaticKeepAliveClientMixin {
  List<dynamic> semesters = [];
  List<dynamic> students = [];
  int? selectedSemesterId;
  bool isLoading = false;
  int currentPage = 1;
  bool hasMoreData = true;
  final TextEditingController studentIdController = TextEditingController();

  @override
  bool get wantKeepAlive => false;

  @override
  void initState() {
    super.initState();
    fetchAnalyticsData();
  }

  @override
  void dispose() {
    // Clear cache when leaving the page
    _clearCache();
    studentIdController.dispose();
    super.dispose();
  }

  Future<void> _clearCache() async {
    try {
      final uri = Uri.http(apiBaseUrl, '/students/at_risk');
      await http.post(
        uri,
        headers: {'Cache-Control': 'no-cache'},
        body: json.encode({'timestamp': DateTime.now().millisecondsSinceEpoch.toString()}),
      );
    } catch (e) {
      print('Error clearing cache: $e');
    }
  }

  Future<void> fetchAnalyticsData() async {
    if (isLoading) return;

    setState(() => isLoading = true);

    try {
      final queryParameters = {
        'page': currentPage.toString(),
        'per_page': '10',
        if (selectedSemesterId != null) 'semester_id': selectedSemesterId.toString(),
      };

      final uri = Uri.http(apiBaseUrl, '/students/at_risk', queryParameters);
      final response = await http.get(uri);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          semesters = data['semesters'];
          students = data['data'];
          hasMoreData = data['data'].isNotEmpty;
        });
      } else {
        throw Exception('Failed to load analytics');
      }
    } catch (e) {
      print('Error: $e');
    } finally {
      setState(() => isLoading = false);
    }
  }

  void onSemesterChanged(int? semesterId) {
    setState(() {
      selectedSemesterId = semesterId;
      students.clear(); // Clear the student list when changing semester
      currentPage = 1; // Reset the page to 1 when changing semester
      hasMoreData = true; // Enable pagination for the new semester
    });
    fetchAnalyticsData();
  }

  void nextPage() {
    if (hasMoreData) {
      setState(() {
        currentPage++;
      });
      fetchAnalyticsData();
    }
  }

  void previousPage() {
    if (currentPage > 1) {
      setState(() {
        currentPage--;
      });
      fetchAnalyticsData();
    }
  }

  Future<void> fetchStudentRiskFactors(String studentId) async {
    if (selectedSemesterId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please select a semester first')),
      );
      return;
    }

    setState(() => isLoading = true);

    try {
      // Use a larger page size to reduce number of API calls
      const int searchPageSize = 50;
      int searchPage = 1;
      bool studentFound = false;
      dynamic foundStudent;
      int maxPages = 3; // Limit the number of pages to search

      while (!studentFound && searchPage <= maxPages) {
        final queryParameters = {
          'page': searchPage.toString(),
          'per_page': searchPageSize.toString(),
          'semester_id': selectedSemesterId.toString(),
        };

        final uri = Uri.http(apiBaseUrl, '/students/at_risk', queryParameters);
        final response = await http.get(uri);

        if (response.statusCode == 200) {
          final data = json.decode(response.body);
          final students = data['data'] as List;
          
          foundStudent = students.firstWhere(
            (s) => s['student']['_id'].toString() == studentId,
            orElse: () => null,
          );

          if (foundStudent != null) {
            studentFound = true;
          } else if (students.isEmpty) {
            break;
          } else {
            searchPage++;
          }
        } else {
          throw Exception('Failed to load student data');
        }
      }

      if (foundStudent != null) {
        final subjects = foundStudent['SubjectCodes'] ?? [];
        final grades = foundStudent['Grades'] ?? [];
        final riskFactors = <String>[];
        
        for (int i = 0; i < subjects.length; i++) {
          final grade = grades[i];
          if (grade <= 79) {
            riskFactors.add('${subjects[i]}: $grade');
          }
        }

        showDialog(
          context: context,
          builder: (BuildContext context) {
            return AlertDialog(
              title: Text('Risk Factor(s)'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: riskFactors.isEmpty
                      ? [Text('No risk factors found for this student')]
                      : riskFactors
                          .map((rf) => Padding(
                                padding: const EdgeInsets.symmetric(vertical: 4.0),
                                child: Text(rf, style: TextStyle(color: Colors.red)),
                              ))
                          .toList(),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () {
                    Navigator.of(context).pop();
                  },
                  child: Text('Close'),
                ),
              ],
            );
          },
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Student Does not have any Failing Grades in the current semester')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Students At Risk (Line of 7 Grades)'),
      ),
      body: isLoading && students.isEmpty
          ? Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: DropdownButtonFormField<int>(
                              value: selectedSemesterId,
                              decoration: InputDecoration(
                                labelText: 'Select Semester',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.calendar_month_rounded),
                              ),
                              items: semesters.map<DropdownMenuItem<int>>((semester) {
                                return DropdownMenuItem<int>(
                                  value: semester['semester_id'],
                                  child: Text('${semester['school_year']} - ${semester['semester_name']}'),
                                );
                              }).toList(),
                              onChanged: onSemesterChanged,
                            ),
                          ),
                          SizedBox(width: 16),
                          Expanded(
                            child: TextField(
                              controller: studentIdController,
                              decoration: InputDecoration(
                                labelText: 'Enter Student ID',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.person),
                              ),
                            ),
                          ),
                          SizedBox(width: 16),
                          ElevatedButton(
                            onPressed: () {
                              if (studentIdController.text.isNotEmpty) {
                                fetchStudentRiskFactors(studentIdController.text);
                              } else {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text('Please enter a student ID')),
                                );
                              }
                            },
                            child: Text('Fetch'),
                            style: ElevatedButton.styleFrom(
                              padding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                            ),
                          ),
                        ],
                      ),
                      SizedBox(height: 8),
                    ],
                  ),
                ),
                Expanded(
                  child: Container(
                    width: 1900,
                    //scrollDirection: Axis.vertical,
                    child: DataTable(
                      decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                  boxShadow: [
                                    BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2))
                                  ],
                                ),
                      columns: const [
                        DataColumn(label: Text('Student ID')),
                        DataColumn(label: Text('Course')),
                        DataColumn(label: Text('Year and Semester')),
                        DataColumn(label: Text('')),
                      ],
                      rows: students.map<DataRow>((student) {
                        final subjects = student['SubjectCodes'] ?? [];
                        final grades = student['Grades'] ?? [];
                        final riskFactors = <String>[];
                        for (int i = 0; i < subjects.length; i++) {
                          final grade = grades[i];
                          if (grade <= 79) {
                            riskFactors.add('${subjects[i]}: $grade');
                          }
                        }
                        return DataRow(cells: [
                          DataCell(Text(student['student']['_id']?.toString() ?? 'Unknown')),
                          DataCell(Text(student['student']['Course'] ?? 'N/A')),
                          DataCell(Text('${student['semester']['SchoolYear']} - ${student['semester']['Semester']}')),
                          DataCell(
                            riskFactors.isNotEmpty
                              ? ElevatedButton(
                                  onPressed: () {
                                    showDialog(
                                      context: context,
                                      builder: (BuildContext context) {
                                        return AlertDialog(
                                          title: Text('Risk Factor(s)'),
                                          content: SingleChildScrollView(
                                            child: Column(
                                              mainAxisSize: MainAxisSize.min,
                                              crossAxisAlignment: CrossAxisAlignment.start,
                                              children: riskFactors
                                                  .map((rf) => Padding(
                                                        padding: const EdgeInsets.symmetric(vertical: 4.0),
                                                        child: Text(rf, style: TextStyle(color: Colors.red)),
                                                      ))
                                                  .toList(),
                                            ),
                                          ),
                                          actions: [
                                            TextButton(
                                              onPressed: () {
                                                Navigator.of(context).pop();
                                              },
                                              child: Text('Close'),
                                            ),
                                          ],
                                        );
                                      },
                                    );
                                  },
                                  child: Text('View Risk Factor(s)'),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.red[100],
                                    foregroundColor: Colors.red[900],
                                  ),
                                )
                              : const Text('None'),
                          ),
                        ]);
                      }).toList(),
                    ),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      ElevatedButton(
                        onPressed: previousPage,
                        child: Text('Previous Page'),
                      ),
                      Text('Page $currentPage', style: TextStyle(fontSize: 12)),
                      ElevatedButton(
                        onPressed: nextPage,
                        child: Text('Next Page'),
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}
