var screen by remember { mutableStateOf(Screen.Home) }
when (screen) { Screen.Home -> Home() }
