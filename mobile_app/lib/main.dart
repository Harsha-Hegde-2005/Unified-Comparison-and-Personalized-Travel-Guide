import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';
import 'screens/map_screen.dart';
import 'screens/login_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/plan_journey_screen.dart';
import 'screens/transit_hub_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  // 1. Unified state notifier variables for settings
  final ValueNotifier<ThemeMode> themeNotifier = ValueNotifier(ThemeMode.light);
  final ValueNotifier<String> mapStyleNotifier = ValueNotifier('standard');
  final ValueNotifier<String> mapProviderNotifier = ValueNotifier('google');

  bool _isLoggedIn = false;

  @override
  Widget build(BuildContext context) {
    // Accent theme color colors matching our website styling
    const primaryColor = Color(0xFF7C5CFF);
    const secondaryColor = Color(0xFF10B981);

    return ValueListenableBuilder<ThemeMode>(
      valueListenable: themeNotifier,
      builder: (context, currentThemeMode, child) {
        return MaterialApp(
          title: 'Commuter Assistant',
          debugShowCheckedModeBanner: false,
          themeMode: currentThemeMode,
          
          // Light Theme Design matching website
          theme: ThemeData(
            useMaterial3: true,
            brightness: Brightness.light,
            scaffoldBackgroundColor: const Color(0xFFF8FAFC),
            primaryColor: primaryColor,
            colorScheme: ColorScheme.fromSeed(
              seedColor: primaryColor,
              primary: primaryColor,
              secondary: secondaryColor,
              brightness: Brightness.light,
              background: const Color(0xFFF8FAFC),
              surface: Colors.white,
            ),
            cardTheme: const CardThemeData(
              color: Colors.white,
              elevation: 2,
            ),
          ),
          
          // Dark Theme Design matching website
          darkTheme: ThemeData(
            useMaterial3: true,
            brightness: Brightness.dark,
            scaffoldBackgroundColor: const Color(0xFF1A1B23),
            primaryColor: primaryColor,
            colorScheme: ColorScheme.fromSeed(
              seedColor: primaryColor,
              primary: primaryColor,
              secondary: secondaryColor,
              brightness: Brightness.dark,
              background: const Color(0xFF1A1B23),
              surface: const Color(0xFF262935),
            ),
            cardTheme: const CardThemeData(
              color: Color(0xFF262935),
              elevation: 2,
            ),
          ),
          
          home: Scaffold(
            body: Builder(
              builder: (context) {
                final screenWidth = MediaQuery.of(context).size.width;
                final isDark = Theme.of(context).brightness == Brightness.dark;

                // Active view based on login state
                Widget activeView;
                if (!_isLoggedIn) {
                  activeView = LoginScreen(
                    onLoginSuccess: (user) {
                      setState(() {
                        _isLoggedIn = true;
                      });
                    },
                  );
                } else {
                  activeView = AppNavigationWrapper(
                    themeNotifier: themeNotifier,
                    mapStyleNotifier: mapStyleNotifier,
                    mapProviderNotifier: mapProviderNotifier,
                  );
                }

                if (screenWidth > 600) {
                  return Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: isDark
                            ? [const Color(0xFF0F172A), const Color(0xFF1E1B4B)]
                            : [const Color(0xFFE2E8F0), const Color(0xFFEEF2F6)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                    ),
                    child: Center(
                      child: Container(
                        width: 440,
                        height: 880,
                        margin: const EdgeInsets.symmetric(vertical: 20),
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF1A1B23) : const Color(0xFFF8FAFC),
                          borderRadius: BorderRadius.circular(40),
                          border: Border.all(
                            color: isDark ? const Color(0xFF334155) : const Color(0xFF94A3B8),
                            width: 12,
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.35),
                              blurRadius: 25,
                              offset: const Offset(0, 12),
                            ),
                          ],
                        ),
                        clipBehavior: Clip.antiAlias,
                        child: activeView,
                      ),
                    ),
                  );
                }

                return activeView;
              },
            ),
          ),
        );
      },
    );
  }
}

class AppNavigationWrapper extends StatefulWidget {
  final ValueNotifier<ThemeMode> themeNotifier;
  final ValueNotifier<String> mapStyleNotifier;
  final ValueNotifier<String> mapProviderNotifier;

  const AppNavigationWrapper({
    super.key,
    required this.themeNotifier,
    required this.mapStyleNotifier,
    required this.mapProviderNotifier,
  });

  @override
  State<AppNavigationWrapper> createState() => _AppNavigationWrapperState();
}

class _AppNavigationWrapperState extends State<AppNavigationWrapper> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final List<Widget> screens = [
      DashboardScreen(
        themeNotifier: widget.themeNotifier,
        mapStyleNotifier: widget.mapStyleNotifier,
        mapProviderNotifier: widget.mapProviderNotifier,
        onNavigateToChat:    () => setState(() => _currentIndex = 3),
        onNavigateToMap:     () => Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => MapScreen(
              mapStyleNotifier: widget.mapStyleNotifier,
              mapProviderNotifier: widget.mapProviderNotifier,
            ),
          ),
        ),
        onNavigateToPlan:    () => setState(() => _currentIndex = 1),
        onNavigateToTransit: () => setState(() => _currentIndex = 2),
      ),
      const PlanJourneyScreen(),
      const TransitHubScreen(),
      const ChatScreen(),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) => setState(() => _currentIndex = index),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.directions_outlined),
            selectedIcon: Icon(Icons.directions),
            label: 'Plan',
          ),
          NavigationDestination(
            icon: Icon(Icons.grid_view_outlined),
            selectedIcon: Icon(Icons.grid_view),
            label: 'Transit',
          ),
          NavigationDestination(
            icon: Icon(Icons.chat_bubble_outline),
            selectedIcon: Icon(Icons.chat_bubble),
            label: 'Assistant',
          ),
        ],
      ),
    );
  }
}
