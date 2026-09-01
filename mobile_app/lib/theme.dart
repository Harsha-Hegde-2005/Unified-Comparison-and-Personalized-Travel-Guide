import 'package:flutter/material.dart';

/// Central Design System tokens mirroring frontend design in App.jsx
class AppTheme {
  // ── Mode Colors ────────────────────────────────────────────────────────────
  static const Color bmtcColor = Color(0xFFF97316); // Orange
  static const Color bmtcBg = Color(0xFF1A0F06);
  static const Color bmtcLightBg = Color(0xFFFFF7ED);

  static const Color metroColor = Color(0xFF8B5CF6); // Purple
  static const Color metroBg = Color(0xFF100C1A);
  static const Color metroLightBg = Color(0xFFF5F3FF);

  static const Color cabColor = Color(0xFFF59E0B); // Amber
  static const Color cabBg = Color(0xFF1A1200);
  static const Color cabLightBg = Color(0xFFFFFBEB);

  static const Color carColor = Color(0xFF10B981); // Emerald Green
  static const Color carBg = Color(0xFF051510);
  static const Color carLightBg = Color(0xFFECFDF5);

  static const Color multimodalColor = Color(0xFFEC4899); // Pink
  static const Color multimodalBg = Color(0xFF1C0D18);
  static const Color multimodalLightBg = Color(0xFFFDF2F8);

  static const Color bicycleColor = Color(0xFF06B6D4); // Cyan
  static const Color bicycleBg = Color(0xFF022329);
  static const Color bicycleLightBg = Color(0xFFECFEFF);

  static const Color walkColor = Color(0xFF6B7A99); // Slate Grey
  static const Color walkBg = Color(0xFF11141A);
  static const Color walkLightBg = Color(0xFFF1F5F9);

  // ── Light Theme Palette ───────────────────────────────────────────────────
  static const Color lightBg = Color(0xFFF4F5FA);
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightCard = Color(0xFFFFFFFF);
  static const Color lightBorder = Color(0xFFEEF0F6);
  static const Color lightBorder2 = Color(0xFFE2E4ED);
  static const Color lightText = Color(0xFF1A1625);
  static const Color lightMuted = Color(0xFF7D788A);
  static const Color lightDim = Color(0xFFF3F1F7);
  static const Color lightAccent = Color(0xFF7C3AED);

  // ── Dark Theme Palette ────────────────────────────────────────────────────
  static const Color darkBg = Color(0xFF090A0F);
  static const Color darkSurface = Color(0xFF12131A);
  static const Color darkCard = Color(0xFF12131A);
  static const Color darkBorder = Color(0xFF1F212E);
  static const Color darkBorder2 = Color(0xFF2D3042);
  static const Color darkText = Color(0xFFF1F3F9);
  static const Color darkMuted = Color(0xFF949BA8);
  static const Color darkDim = Color(0xFF171923);
  static const Color darkAccent = Color(0xFFA855F7);

  // ── Functional Colors ─────────────────────────────────────────────────────
  static const Color green = Color(0xFF10B981);
  static const Color red = Color(0xFFEF4444);
  static const Color yellow = Color(0xFFF59E0B);
  static const Color blue = Color(0xFF3B82F6);

  // ── Helper getters based on brightness ────────────────────────────────────
  static Color getBg(bool isDark) => isDark ? darkBg : lightBg;
  static Color getSurface(bool isDark) => isDark ? darkSurface : lightSurface;
  static Color getCard(bool isDark) => isDark ? darkCard : lightCard;
  static Color getBorder(bool isDark) => isDark ? darkBorder : lightBorder;
  static Color getBorder2(bool isDark) => isDark ? darkBorder2 : lightBorder2;
  static Color getText(bool isDark) => isDark ? darkText : lightText;
  static Color getMuted(bool isDark) => isDark ? darkMuted : lightMuted;
  static Color getDim(bool isDark) => isDark ? darkDim : lightDim;
  static Color getAccent(bool isDark) => isDark ? darkAccent : lightAccent;

  // ── Mode Metadata ─────────────────────────────────────────────────────────
  static Color getModeColor(String mode) {
    switch (mode.toLowerCase()) {
      case 'bmtc':
      case 'bus':
        return bmtcColor;
      case 'metro':
        return metroColor;
      case 'cab':
      case 'auto':
        return cabColor;
      case 'car':
      case 'vehicle':
        return carColor;
      case 'multimodal':
      case 'multi':
        return multimodalColor;
      case 'bicycle':
      case 'cycle':
        return bicycleColor;
      case 'walk':
        return walkColor;
      default:
        return lightAccent;
    }
  }

  static Color getModeBg(String mode, bool isDark) {
    final c = getModeColor(mode);
    return isDark ? c.withValues(alpha: 0.15) : c.withValues(alpha: 0.08);
  }

  static String getModeLabel(String mode) {
    switch (mode.toLowerCase()) {
      case 'bmtc':
      case 'bus':
        return 'BMTC Bus';
      case 'metro':
        return 'Namma Metro';
      case 'cab':
      case 'auto':
        return 'Cab / Auto';
      case 'car':
      case 'vehicle':
        return 'Personal Vehicle';
      case 'multimodal':
      case 'multi':
        return 'Multimodal Transit';
      case 'bicycle':
      case 'cycle':
        return 'Cycling';
      case 'walk':
        return 'Walking';
      default:
        return mode.toUpperCase();
    }
  }

  static IconData getModeIcon(String mode) {
    switch (mode.toLowerCase()) {
      case 'bmtc':
      case 'bus':
        return Icons.directions_bus_rounded;
      case 'metro':
        return Icons.subway_rounded;
      case 'cab':
      case 'auto':
        return Icons.local_taxi_rounded;
      case 'car':
      case 'vehicle':
        return Icons.directions_car_rounded;
      case 'multimodal':
      case 'multi':
        return Icons.alt_route_rounded;
      case 'bicycle':
      case 'cycle':
        return Icons.pedal_bike_rounded;
      case 'walk':
        return Icons.directions_walk_rounded;
      default:
        return Icons.navigation_rounded;
    }
  }

  // ── ThemeData Generators ──────────────────────────────────────────────────
  static ThemeData get lightThemeData {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: lightBg,
      primaryColor: lightAccent,
      colorScheme: const ColorScheme.light(
        primary: lightAccent,
        secondary: green,
        surface: lightSurface,
        onSurface: lightText,
        outline: lightBorder,
      ),
      cardTheme: CardThemeData(
        color: lightCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: lightBorder),
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: lightSurface,
        foregroundColor: lightText,
        elevation: 0,
        centerTitle: false,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: lightSurface,
        selectedItemColor: lightAccent,
        unselectedItemColor: lightMuted,
      ),
    );
  }

  static ThemeData get darkThemeData {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBg,
      primaryColor: darkAccent,
      colorScheme: const ColorScheme.dark(
        primary: darkAccent,
        secondary: green,
        surface: darkSurface,
        onSurface: darkText,
        outline: darkBorder,
      ),
      cardTheme: CardThemeData(
        color: darkCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: darkBorder),
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: darkSurface,
        foregroundColor: darkText,
        elevation: 0,
        centerTitle: false,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: darkSurface,
        selectedItemColor: darkAccent,
        unselectedItemColor: darkMuted,
      ),
    );
  }
}

/// A stylish badge/pill matching the website UI
class PillBadge extends StatelessWidget {
  final String text;
  final Color color;
  final bool isSmall;
  final IconData? icon;

  const PillBadge({
    super.key,
    required this.text,
    required this.color,
    this.isSmall = false,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isSmall ? 8 : 10,
        vertical: isSmall ? 2 : 4,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: isSmall ? 10 : 12, color: color),
            const SizedBox(width: 4),
          ],
          Text(
            text,
            style: TextStyle(
              color: color,
              fontSize: isSmall ? 10 : 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.2,
            ),
          ),
        ],
      ),
    );
  }
}
