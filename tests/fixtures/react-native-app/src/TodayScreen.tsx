import { Dimensions, Image, Pressable, SafeAreaView, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

export function TodayScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title} allowFontScaling={false}>Today</Text>
      <Pressable onPress={() => {}} style={styles.add}>
        <Ionicons name="add" size={22} color="#ffffff" />
      </Pressable>
      <Pressable onPress={() => {}}>
        <Text>Plan sprint</Text>
      </Pressable>
      <Image source={require('./hero.png')} style={{ width }} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#ffffff', paddingLeft: 16 },
  title: { fontSize: 34, color: '#111111', textAlign: 'left' },
  add: { marginLeft: 8, backgroundColor: '#0A84FF' },
});
