import React from 'react';

export const appStyles: {[key: string]: React.CSSProperties} = {
    loadingScreen: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', width: '100vw', fontSize: '1.5em', color: 'var(--primary-text-color)', backgroundColor: 'var(--background-color)' },
    appContainer: { display: 'flex', width: '100%' },
    mainContent: { flexGrow: 1, padding: '20px', display: 'flex', flexDirection: 'column' },
    error: { color: '#ff8a80', backgroundColor: '#4d2a2a', padding: '10px', borderRadius: '4px', textAlign: 'center' },
};
