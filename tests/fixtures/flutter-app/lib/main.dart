import 'package:flutter/material.dart';

void main() => runApp(const HabitsApp());

class HabitsApp extends StatelessWidget {
  const HabitsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      theme: ThemeData(colorSchemeSeed: const Color(0xFF3355AA)),
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(textScaler: TextScaler.noScaling),
        child: child!,
      ),
      home: const TodayScreen(),
    );
  }
}

class TodayScreen extends StatefulWidget {
  const TodayScreen({super.key});
  @override
  State<TodayScreen> createState() => _TodayScreenState();
}

class _TodayScreenState extends State<TodayScreen> {
  bool reminders = true;
  int tab = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Today'),
        actions: [IconButton(icon: const Icon(Icons.add), onPressed: () {})],
      ),
      body: ListView(
        padding: const EdgeInsets.only(left: 16, right: 8),
        children: [
          Image.asset('assets/hero.png'),
          SwitchListTile(value: reminders, onChanged: (v) => setState(() => reminders = v), title: const Text('Reminders')),
          Switch(value: reminders, onChanged: (v) => setState(() => reminders = v)),
          const CircularProgressIndicator(),
          GestureDetector(onTap: () {}, child: const Icon(Icons.more_horiz)),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: tab,
        onTap: (i) => setState(() => tab = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.today), label: 'Today'),
          BottomNavigationBarItem(icon: Icon(Icons.insights), label: 'Insights'),
        ],
      ),
    );
  }
}
