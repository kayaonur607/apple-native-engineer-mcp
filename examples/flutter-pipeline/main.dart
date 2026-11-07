// Habits — a controlled Flutter demo for the Apple-native pipeline.
//
// What makes it read as an iPhone app, and what audit_cross_platform checks:
//   * Cupertino tab bar on iOS, Material NavigationBar elsewhere (FLT003)
//   * .adaptive() controls, so iOS gets CupertinoSwitch / activity indicator (FLT002)
//   * darkTheme + ThemeMode.system, so Dark Mode follows the device (FLT007)
//   * no text-scaling override, so Dynamic Type works (FLT001)
//   * tooltips on icon buttons, which become VoiceOver labels (FLT004)
//   * EdgeInsetsDirectional, so right-to-left languages mirror (FLT008)
//   * English and Turkish, also registered in Xcode's knownRegions (FLT009)
//
// capture_screenshots routes to a screen with the same launch argument the Swift
// and React Native examples use: `-screen insights`. iOS places launch arguments
// in the NSUserDefaults argument domain, which SharedPreferencesAsync reads. Two
// alternatives were tried in the Simulator and rejected: Platform.environment is
// empty for Flutter apps on iOS, and custom-scheme deep links opened by simctl
// show an "Open in …?" confirmation that would end up in the screenshot.

import 'dart:io' show Platform;

import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:shared_preferences/shared_preferences.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final screen = await SharedPreferencesAsync().getString('screen');
  runApp(HabitsApp(initialScreen: screen == 'insights' ? 1 : 0));
}

class Strings {
  const Strings(this.today, this.insights, this.focus, this.reminders, this.done, this.streak, this.addHabit);
  final String today, insights, focus, reminders, done, streak, addHabit;

  static Strings of(BuildContext context) => Localizations.localeOf(context).languageCode == 'tr'
      ? const Strings('Bugün', 'Özet', 'Odak', 'Hatırlatıcılar', 'tamamlandı', 'günlük seri', 'Alışkanlık ekle')
      : const Strings('Today', 'Insights', 'Focus', 'Reminders', 'done', 'day streak', 'Add habit');
}

class HabitsApp extends StatelessWidget {
  const HabitsApp({super.key, this.initialScreen = 0});
  final int initialScreen;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorSchemeSeed: const Color(0xFF0A84FF), brightness: Brightness.light),
      darkTheme: ThemeData(colorSchemeSeed: const Color(0xFF0A84FF), brightness: Brightness.dark),
      themeMode: ThemeMode.system,
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      supportedLocales: const [Locale('en'), Locale('tr')],
      home: Home(initial: initialScreen),
    );
  }
}

class Home extends StatefulWidget {
  const Home({super.key, required this.initial});
  final int initial;
  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  late int tab = widget.initial;

  @override
  Widget build(BuildContext context) {
    final s = Strings.of(context);
    final pages = [TodayPage(strings: s), InsightsPage(strings: s)];
    final items = [
      BottomNavigationBarItem(icon: const Icon(CupertinoIcons.sun_max), label: s.today),
      BottomNavigationBarItem(icon: const Icon(CupertinoIcons.chart_bar), label: s.insights),
    ];
    return Scaffold(
      body: pages[tab],
      bottomNavigationBar: Platform.isIOS
          ? CupertinoTabBar(currentIndex: tab, onTap: (i) => setState(() => tab = i), items: items)
          : NavigationBar(
              selectedIndex: tab,
              onDestinationSelected: (i) => setState(() => tab = i),
              destinations: [
                for (final item in items) NavigationDestination(icon: item.icon, label: item.label!),
              ],
            ),
    );
  }
}

class TodayPage extends StatefulWidget {
  const TodayPage({super.key, required this.strings});
  final Strings strings;
  @override
  State<TodayPage> createState() => _TodayPageState();
}

class _TodayPageState extends State<TodayPage> {
  final done = {'Design review': true, 'Ship build 42': false, 'Plan sprint': false};
  bool reminders = true;

  @override
  Widget build(BuildContext context) {
    final s = widget.strings;
    return CustomScrollView(slivers: [
      SliverAppBar.large(
        title: Text(s.today),
        actions: [IconButton(tooltip: s.addHabit, icon: const Icon(CupertinoIcons.add), onPressed: () {})],
      ),
      SliverList.list(children: [
        _Header(s.focus),
        for (final entry in done.entries)
          CheckboxListTile.adaptive(
            value: entry.value,
            title: Text(entry.key),
            onChanged: (value) => setState(() => done[entry.key] = value ?? false),
          ),
        const Divider(),
        SwitchListTile.adaptive(
          value: reminders,
          title: Text(s.reminders),
          onChanged: (value) => setState(() => reminders = value),
        ),
      ]),
    ]);
  }
}

class InsightsPage extends StatelessWidget {
  const InsightsPage({super.key, required this.strings});
  final Strings strings;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return CustomScrollView(slivers: [
      SliverAppBar.large(title: Text(strings.insights)),
      SliverPadding(
        padding: const EdgeInsetsDirectional.fromSTEB(20, 8, 20, 20),
        sliver: SliverList.list(children: [
          Text('27', style: theme.textTheme.displayLarge),
          Text('${strings.streak} · 72% ${strings.done}', style: theme.textTheme.titleMedium),
          const SizedBox(height: 24),
          LinearProgressIndicator(value: 0.72, minHeight: 10, borderRadius: BorderRadius.circular(5)),
        ]),
      ),
    ]);
  }
}

class _Header extends StatelessWidget {
  const _Header(this.text);
  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsetsDirectional.fromSTEB(16, 8, 16, 4),
        child: Text(text, style: Theme.of(context).textTheme.titleSmall),
      );
}
