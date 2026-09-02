import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/map_theme_service.dart';

void showAppSettingsModal(
  BuildContext context, {
  ValueNotifier<ThemeMode>? themeNotifier,
  ValueNotifier<String>? mapStyleNotifier,
  ValueNotifier<String>? mapProviderNotifier,
}) {
  final urlCtrl = TextEditingController(text: ApiService.baseUrl);

  final activeStyleNotifier = mapStyleNotifier ?? MapThemeService.mapStyleNotifier;
  final activeProviderNotifier = mapProviderNotifier ?? MapThemeService.mapProviderNotifier;

  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (context) {
      return StatefulBuilder(
        builder: (context, setModalState) {
          final currentTheme = themeNotifier?.value ?? ThemeMode.dark;
          final currentStyle = activeStyleNotifier.value;
          final currentProvider = activeProviderNotifier.value;

          Widget buildPillOption({
            required String label,
            required String emoji,
            required bool isSelected,
            required VoidCallback onTap,
          }) {
            return Expanded(
              child: InkWell(
                onTap: onTap,
                borderRadius: BorderRadius.circular(14),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
                  decoration: BoxDecoration(
                    color: isSelected ? const Color(0xFF22163B) : const Color(0xFF161824),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: isSelected ? const Color(0xFFA855F7) : const Color(0xFF2A2D40),
                      width: isSelected ? 2 : 1.2,
                    ),
                    boxShadow: isSelected
                        ? [
                            BoxShadow(
                              color: const Color(0xFFA855F7).withValues(alpha: 0.25),
                              blurRadius: 8,
                              spreadRadius: 1,
                            ),
                          ]
                        : [],
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(emoji, style: const TextStyle(fontSize: 16)),
                      const SizedBox(width: 8),
                      Text(
                        label,
                        style: TextStyle(
                          color: isSelected ? Colors.white : const Color(0xFF94A3B8),
                          fontSize: 13,
                          fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          }

          Widget buildGridThemeCard({
            required String title,
            required IconData icon,
            required String styleKey,
          }) {
            final isSelected = currentStyle == styleKey;
            return InkWell(
              onTap: () {
                activeStyleNotifier.value = styleKey;
                MapThemeService.mapStyle = styleKey;
                setModalState(() {});
              },
              borderRadius: BorderRadius.circular(16),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                decoration: BoxDecoration(
                  color: isSelected ? const Color(0xFF201639) : const Color(0xFF151722),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: isSelected ? const Color(0xFFA855F7) : const Color(0xFF26293A),
                    width: isSelected ? 2 : 1.2,
                  ),
                  boxShadow: isSelected
                      ? [
                          BoxShadow(
                            color: const Color(0xFFA855F7).withValues(alpha: 0.3),
                            blurRadius: 10,
                            spreadRadius: 1,
                          ),
                        ]
                      : [],
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: isSelected ? const Color(0xFFA855F7).withValues(alpha: 0.2) : const Color(0xFF202336),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        icon,
                        color: isSelected ? const Color(0xFFA855F7) : const Color(0xFF94A3B8),
                        size: 22,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      title,
                      style: TextStyle(
                        color: isSelected ? Colors.white : const Color(0xFFCBD5E1),
                        fontSize: 12,
                        fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }

          return Container(
            decoration: const BoxDecoration(
              color: Color(0xFF10121B),
              borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
            ),
            padding: EdgeInsets.only(
              bottom: MediaQuery.of(context).viewInsets.bottom + 24,
              left: 20,
              right: 20,
              top: 16,
            ),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Top Handle Bar
                  Center(
                    child: Container(
                      width: 42,
                      height: 5,
                      decoration: BoxDecoration(
                        color: const Color(0xFF2F344A),
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Header with Close X Button
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'App Settings',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.w900,
                          letterSpacing: 0.3,
                        ),
                      ),
                      IconButton(
                        onPressed: () => Navigator.pop(context),
                        icon: const Icon(Icons.close_rounded, color: Color(0xFF94A3B8), size: 24),
                        tooltip: 'Close Settings',
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // 1. APP INTERFACE THEME
                  const Text(
                    'APP INTERFACE THEME',
                    style: TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.8,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      buildPillOption(
                        label: 'Light Mode',
                        emoji: '☀️',
                        isSelected: currentTheme == ThemeMode.light,
                        onTap: () {
                          if (themeNotifier != null) themeNotifier.value = ThemeMode.light;
                          setModalState(() {});
                        },
                      ),
                      const SizedBox(width: 12),
                      buildPillOption(
                        label: 'Dark Mode',
                        emoji: '🌙',
                        isSelected: currentTheme == ThemeMode.dark,
                        onTap: () {
                          if (themeNotifier != null) themeNotifier.value = ThemeMode.dark;
                          setModalState(() {});
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // 2. MAP STYLE THEME (2x2 Grid)
                  const Text(
                    'MAP STYLE THEME',
                    style: TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.8,
                    ),
                  ),
                  const SizedBox(height: 12),
                  GridView.count(
                    crossAxisCount: 2,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 1.55,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    children: [
                      buildGridThemeCard(
                        title: 'Dark Mode Map',
                        icon: Icons.dark_mode_rounded,
                        styleKey: 'dark',
                      ),
                      buildGridThemeCard(
                        title: 'Light Mode Map',
                        icon: Icons.wb_sunny_rounded,
                        styleKey: 'standard',
                      ),
                      buildGridThemeCard(
                        title: 'Satellite View',
                        icon: Icons.satellite_alt_rounded,
                        styleKey: 'satellite',
                      ),
                      buildGridThemeCard(
                        title: 'Terrain View',
                        icon: Icons.terrain_rounded,
                        styleKey: 'terrain',
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // 3. MAP ENGINE PROVIDER
                  const Text(
                    'MAP ENGINE PROVIDER',
                    style: TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.8,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      buildPillOption(
                        label: 'Google Maps',
                        emoji: '🗺️',
                        isSelected: currentProvider == 'google',
                        onTap: () {
                          activeProviderNotifier.value = 'google';
                          MapThemeService.mapProvider = 'google';
                          setModalState(() {});
                        },
                      ),
                      const SizedBox(width: 12),
                      buildPillOption(
                        label: 'OpenStreetMap',
                        emoji: '🌍',
                        isSelected: currentProvider == 'osm',
                        onTap: () {
                          activeProviderNotifier.value = 'osm';
                          MapThemeService.mapProvider = 'osm';
                          setModalState(() {});
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // 4. BACKEND SERVER CONFIGURATION
                  const Text(
                    'BACKEND SERVER CONFIGURATION',
                    style: TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.8,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFF161824),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: const Color(0xFF2A2D40)),
                    ),
                    child: TextField(
                      controller: urlCtrl,
                      style: const TextStyle(color: Colors.white, fontSize: 13),
                      decoration: const InputDecoration(
                        border: InputBorder.none,
                        hintText: 'http://localhost:8000',
                        hintStyle: TextStyle(color: Color(0xFF64748B)),
                        prefixIcon: Icon(Icons.dns_rounded, color: Color(0xFFA855F7), size: 20),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {
                        final val = urlCtrl.text.trim();
                        if (val.isNotEmpty) {
                          ApiService.baseUrl = val;
                        }
                        Navigator.pop(context);
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFA855F7),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        elevation: 4,
                      ),
                      child: const Text(
                        'Save Configuration',
                        style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      );
    },
  );
}
