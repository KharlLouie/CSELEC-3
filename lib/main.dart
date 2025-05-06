import 'dart:convert';
import 'package:finals/StudentAtRisk.dart';
import 'package:finals/SubjectAnalytics.dart';
import 'package:finals/SubjectPerformance.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() => runApp(StudentDashboardApp());

class StudentDashboardApp extends StatelessWidget {
  const StudentDashboardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: StudentDashboard(),
    );
  }
}

class StudentDashboard extends StatefulWidget {
  const StudentDashboard({super.key});

  @override
  _StudentDashboardState createState() => _StudentDashboardState();
}

class _StudentDashboardState extends State<StudentDashboard> with SingleTickerProviderStateMixin {
  final Color primaryColor = Color(0xFF5A67D8);
  final Color backgroundColor = Color(0xFFF7FAFC);
  late AnimationController _controller;
  late Animation<Offset> _slideAnimation;
  bool _isDrawerOpen = false;

  int? selectedSchoolYear;
  String? selectedSemester;

  List<int> schoolYears = [];
  final List<String> semesters = ['FirstSem', 'SecondSem', 'Summer'];

  double? passingRate;
  double? atRiskRate;
  double? averageGrade;
  double? topGrade;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: Duration(milliseconds: 300),
      vsync: this,
    );
    _slideAnimation = Tween<Offset>(
      begin: Offset(-1.0, 0.0),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));

    fetchSchoolYears();
  }

  void _toggleSidebar() {
    setState(() {
      if (_isDrawerOpen) {
        _controller.reverse();
      } else {
        _controller.forward();
      }
      _isDrawerOpen = !_isDrawerOpen;
    });
  }

  Future<void> fetchSchoolYears() async {
    final url = Uri.parse('http://127.0.0.1:5000/home/');
    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          schoolYears = List<int>.from(data['school_years']);
        });
      }
    } catch (e) {
      print("Error fetching school years: $e");
    }
  }

  Future<void> fetchSemesterData() async {
    if (selectedSchoolYear == null || selectedSemester == null) return;

    final url = Uri.parse('http://127.0.0.1:5000/home/?sy=$selectedSchoolYear');

    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List semestersData = data['semesters'];

        final semesterData = semestersData.firstWhere(
          (s) => s['semester_name'] == selectedSemester,
          orElse: () => null,
        );

        if (semesterData != null) {
          setState(() {
            passingRate = semesterData['passing_rate']?.toDouble();
            atRiskRate = semesterData['at_risk_rate']?.toDouble();
            averageGrade = semesterData['average_grade']?.toDouble();
            topGrade = semesterData['top_grade']?.toDouble();
          });
        }
      } else {
        print("Failed to fetch data. Status code: ${response.statusCode}");
      }
    } catch (e) {
      print("Error fetching semester data: $e");
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: backgroundColor,
      body: Stack(
        children: [
          Row(
            children: [
              SlideTransition(
                position: _slideAnimation,
                child: Container(
                  width: 250,
                  color: primaryColor,
                  padding: EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
children: [
  SizedBox(height: 90),
    Text(
      'Commands',
      style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
    ),
  SizedBox(height: 20),
  GestureDetector(
    onTap: () {Navigator.push(context, MaterialPageRoute(builder: (context) => StudentPerformancePage()));},
    child: Text(
      'Subject Performance',
      style: TextStyle(color: Colors.white),
    ),
  ),
  SizedBox(height: 10),
  GestureDetector(
    onTap: () {Navigator.push(context, MaterialPageRoute(builder: (context) => StudentRiskAnalyticsPage()));},
    child: Text(
      'At-Risk Student List',
      style: TextStyle(color: Colors.white),
    ),
  ),
  SizedBox(height: 10),
  GestureDetector(
    onTap: () {Navigator.push(context, MaterialPageRoute(builder: (context) => SubjectAnalyticsPage()));},
    child: Text(
      'Subject Analytics',
      style: TextStyle(color: Colors.white),
    ),
  ),
  SizedBox(height: 10),
  GestureDetector(
    onTap: () {},
    child: Text(
      'Modify Data',
      style: TextStyle(color: Colors.white),
    ),
  ),
],
                  ),
                ),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Performance Dashboard', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.black87)),
                      SizedBox(height: 20),

                      // School Year Dropdown
                      Text('School Year:', style: TextStyle(color: Colors.black, fontSize: 16, fontWeight: FontWeight.bold)),
                      SizedBox(height: 8),
                      Container(
                        padding: EdgeInsets.symmetric(horizontal: 16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                          boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2))],
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<int>(
                            value: selectedSchoolYear,
                            hint: Text("Select School Year"),
                            onChanged: (value) {
                              setState(() {
                                selectedSchoolYear = value;
                                selectedSemester = null;
                              });
                            },
                            items: schoolYears.map((year) {
                              return DropdownMenuItem<int>(
                                value: year,
                                child: Text(year.toString()),
                              );
                            }).toList(),
                          ),
                        ),
                      ),

                      SizedBox(height: 20),

                      // Semester Dropdown
                      Text('Semester:', style: TextStyle(color: Colors.black, fontSize: 16, fontWeight: FontWeight.bold)),
                      SizedBox(height: 8),
                      Container(
                        padding: EdgeInsets.symmetric(horizontal: 16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                          boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 6, offset: Offset(0, 2))],
                        ),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            value: selectedSemester,
                            hint: Text("Select Semester"),
                            onChanged: (value) {
                              setState(() {
                                selectedSemester = value;
                              });
                            },
                            items: semesters.map((sem) {
                              return DropdownMenuItem<String>(
                                value: sem,
                                child: Text(sem),
                              );
                            }).toList(),
                          ),
                        ),
                      ),

                      SizedBox(height: 20),

                      ElevatedButton(
                        onPressed: fetchSemesterData,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: primaryColor,
                          padding: EdgeInsets.symmetric(horizontal: 32, vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        child: Text('Fetch Data', style: TextStyle(fontSize: 16, color: Colors.white)),
                      ),

                      SizedBox(height: 30),

                      Row(
                        children: [
                          _buildMetricCard('Passing Rate', passingRate),
                          SizedBox(width: 20),
                          _buildMetricCard('At-Risk Rate', atRiskRate),
                        ],
                      ),
                      SizedBox(height: 30),
                      Expanded(
                        child: Row(
                          children: [
                            Expanded(
                              child: _buildMetricCard('Average Grade', averageGrade),
                            ),
                            SizedBox(width: 20),
                            Expanded(
                              child: _buildMetricCard('Top Grade', topGrade),
                            ),
                          ],
                        ),
                      )
                    ],
                  ),
                ),
              ),
            ],
          ),
          Positioned(
            top: 40,
            left: 20,
            child: IconButton(
              icon: Icon(Icons.menu, color: Colors.black, size: 40),
              onPressed: _toggleSidebar,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricCard(String title, double? value) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 20.0, horizontal: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: TextStyle(fontSize: 16, color: Colors.grey[700])),
            SizedBox(height: 10),
            Text(value?.toStringAsFixed(2) ?? 'N/A', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }
}
