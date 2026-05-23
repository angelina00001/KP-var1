# 📱 Мобильный клиент для 2FA Service

Для получения push-уведомлений необходимо мобильное приложение. Ниже приведены примеры реализации на разных платформах.

## React Native (iOS/Android)

```javascript
// App.js
import messaging from '@react-native-firebase/messaging';
import { useState, useEffect } from 'react';

async function requestUserPermission() {
  const authStatus = await messaging().requestPermission();
  return authStatus === messaging.AuthorizationStatus.AUTHORIZED;
}

async function getFCMToken() {
  const token = await messaging().getToken();
  console.log('FCM Token:', token);
  return token;
}

// Отправка токена на сервер при регистрации
async function registerWithPush(email, password, fcmToken) {
  const response = await fetch('http://localhost:8000/api/v1/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      password,
      full_name: "Mobile User",
      tfa_enabled: true,
      device_type: "push",
      device_name: "My iPhone",
      fcm_token: fcmToken
    })
  });
  return response.json();
}

// Обработка push-уведомления 2FA
messaging().onMessage(async (remoteMessage) => {
  if (remoteMessage.data?.type === '2fa_challenge') {
    const { nonce } = remoteMessage.data;
    // Показать диалог пользователю
    Alert.alert(
      '2FA Authentication',
      'Approve sign-in attempt?',
      [
        { text: 'Deny', onPress: () => console.log('Denied') },
        { 
          text: 'Approve', 
          onPress: () => approveLogin(nonce) 
        }
      ]
    );
  }
});

async function approveLogin(nonce) {
  const response = await fetch('http://localhost:8000/api/v1/tfa/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      push_nonce: nonce
    })
  });
  // Send to server...
}