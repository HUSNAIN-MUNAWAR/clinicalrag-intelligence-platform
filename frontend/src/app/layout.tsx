import './globals.css';
import Shell from '@/components/Shell';
export const metadata = { title: 'ClinicalRAG Intelligence Platform', description: 'Advanced medical RAG portfolio platform' };
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><Shell>{children}</Shell></body></html>}
