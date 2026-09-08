const [screen, setScreen] = useState('home');
function AppNavigator() { return screen === 'home' ? <Home/> : <Detail/>; }
