import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';
import 'screens/map_screen.dart';
import 'screens/login_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/plan_journey_screen.dart';
import 'screens/transit_hub_screen.dart';
import 'theme.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  final ValueNotifier<ThemeMode> themeNotifier = ValueNotifier(ThemeMode.light);
  final ValueNotifier<String> mapStyleNotifier = ValueNotifier('standard');
  final ValueNotifier<String> mapProviderNotifier = ValueNotifier('google');

  bool _isLoggedIn = false;
  String _currentUsername = '';

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<ThemeMode>(
      valueListenable: themeNotifier,
      builder: (context, currentThemeMode, child) {
        return MaterialApp(
          title: 'Bengaluru Commuter Assistant',
          debugShowCheckedModeBanner: false,
          themeMode: currentThemeMode,
          theme: AppTheme.lightThemeData,
          darkTheme: AppTheme.darkThemeData,
          builder: (context, childWidget) {
            return LayoutBuilder(
              builder: (context, constraints) {
                final isDark = Theme.of(context).brightness == Brightness.dark;
                final screenWidth = constraints.maxWidth;
                final screenHeight = constraints.maxHeight;

                if (screenWidth > 500) {
                  return Container(
                    width: double.infinity,
                    height: double.infinity,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: isDark
                            ? [const Color(0xFF0B0D14), const Color(0xFF151824)]
                            : [const Color(0xFFE2E8F0), const Color(0xFFEEF2F6)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                    ),
                    child: Center(
                      child: Container(
                        width: 412,
                        height: screenHeight > 880 ? 860 : screenHeight - 32,
                        margin: const EdgeInsets.symmetric(vertical: 16),
                        decoration: BoxDecoration(
                          color: isDark ? AppTheme.darkBg : AppTheme.lightBg,
                          borderRadius: BorderRadius.circular(42),
                          border: Border.all(
                            color: isDark ? const Color(0xFF2A2D3D) : const Color(0xFFCBD5E1),
                            width: 10,
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withValues(alpha: isDark ? 0.6 : 0.25),
                              blurRadius: 35,
                              spreadRadius: 2,
                              offset: const Offset(0, 15),
                            ),
                          ],
                        ),
                        clipBehavior: Clip.antiAlias,
                        child: Column(
                          children: [
                            // Sleek phone speaker / notch bar
                            Container(
                              height: 24,
                              color: isDark ? AppTheme.darkCard : AppTheme.lightCard,
                              child: Center(
                                child: Container(
                                  width: 90,
                                  height: 4,
                                  decoration: BoxDecoration(
                                    color: isDark ? Colors.grey.shade700 : Colors.grey.shade400,
                                    borderRadius: BorderRadius.circular(2),
                                  ),
                                ),
                              ),
                            ),
                            // Pushed screens and active view
                            Expanded(child: childWidget ?? const SizedBox()),
                          ],
                        ),
                      ),
                    ),
                  );
                }
                return childWidget ?? const SizedBox();
              },
            );
          },
          home: _isLoggedIn
              ? AppNavigationWrapper(
                  themeNotifier: themeNotifier,
                  mapStyleNotifier: mapStyleNotifier,
                  mapProviderNotifier: mapProviderNotifier,
                  username: _currentUsername,
                  onOpenLogin: () {
                    setState(() => _isLoggedIn = false);
                  },
                )
              : LoginScreen(
                  onLoginSuccess: (user) {
                    setState(() {
                      _currentUsername = user;
                      _isLoggedIn = true;
                    });
                  },
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
  final String username;
  final VoidCallback onOpenLogin;

  const AppNavigationWrapper({
    super.key,
    required this.themeNotifier,
    required this.mapStyleNotifier,
    required this.mapProviderNotifier,
    required this.username,
    required this.onOpenLogin,
  });

  @override
  State<AppNavigationWrapper> createState() => _AppNavigationWrapperState();
}

class _AppNavigationWrapperState extends State<AppNavigationWrapper> {
  int _currentIndex = 0;
  int _transitTabIndex = 0;
  String? _prefillSource;
  String? _prefillDestination;

  void _navigateToPlanWithRoute(Map<String, String> route) {
    setState(() {
      _prefillSource = route['source'];
      _prefillDestination = route['destination'];
      _currentIndex = 1;
    });
  }

  void _navigateToTransitWithTab(int tabIndex) {
    setState(() {
      _transitTabIndex = tabIndex;
      _currentIndex = 2;
    });
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      DashboardScreen(
        themeNotifier: widget.themeNotifier,
        mapStyleNotifier: widget.mapStyleNotifier,
        mapProviderNotifier: widget.mapProviderNotifier,
        username: widget.username,
        onOpenLogin: widget.onOpenLogin,
        onNavigateToChat: () => setState(() => _currentIndex = 3),
        onNavigateToMap: () => Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => MapScreen(
              mapStyleNotifier: widget.mapStyleNotifier,
              mapProviderNotifier: widget.mapProviderNotifier,
            ),
          ),
        ),
        onNavigateToPlanWithRoute: _navigateToPlanWithRoute,
        onNavigateToTransit: () => _navigateToTransitWithTab(0),
        onNavigateToTransitWithTab: _navigateToTransitWithTab,
      ),
      PlanJourneyScreen(
        key: ValueKey('$_prefillSource-$_prefillDestination'),
        initialSource: _prefillSource,
        initialDestination: _prefillDestination,
      ),
      TransitHubScreen(
        key: ValueKey('transit-$_transitTabIndex'),
        initialTabIndex: _transitTabIndex,
      ),
      ChatScreen(
        onPlanJourney: _navigateToPlanWithRoute,
      ),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
            if (index != 1) {
              _prefillSource = null;
              _prefillDestination = null;
            }
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.grid_view_rounded),
            selectedIcon: Icon(Icons.grid_view_rounded, color: AppTheme.bmtcColor),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.directions_rounded),
            selectedIcon: Icon(Icons.directions_rounded, color: AppTheme.bmtcColor),
            label: 'Plan',
          ),
          NavigationDestination(
            icon: Icon(Icons.directions_bus_rounded),
            selectedIcon: Icon(Icons.directions_bus_rounded, color: AppTheme.bmtcColor),
            label: 'Transit',
          ),
          NavigationDestination(
            icon: Icon(Icons.chat_bubble_outline_rounded),
            selectedIcon: Icon(Icons.chat_bubble_rounded, color: AppTheme.bmtcColor),
            label: 'Assistant',
          ),
        ],
      ),
    );
  }
}
