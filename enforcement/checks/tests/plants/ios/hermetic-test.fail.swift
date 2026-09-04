let (data, _) = try await URLSession.shared.data(from: URL(string: "https://api.weather.example-live.com/now")!)
