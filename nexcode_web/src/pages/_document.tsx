import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="zh-CN">
      <Head>
        <meta charSet="utf-8" />
        <meta name="description" content="NexCode - 智能AI编程助手，提升您的开发效率" />
        <meta name="keywords" content="AI,编程,代码助手,开发工具,NexCode" />
        <meta name="author" content="NexCode Team" />
        
        {/* 使用logo作为favicon */}
        <link rel="icon" href="/logo.png" type="image/png" />
        <link rel="apple-touch-icon" href="/logo.png" />
        
        {/* Open Graph meta tags */}
        <meta property="og:title" content="NexCode - 智能AI编程助手" />
        <meta property="og:description" content="智能代码助手，帮助您提高开发效率。支持代码生成、审查、错误诊断和智能对话。" />
        <meta property="og:image" content="/logo.png" />
        <meta property="og:type" content="website" />
        
        {/* Twitter Card meta tags */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="NexCode - 智能AI编程助手" />
        <meta name="twitter:description" content="智能代码助手，帮助您提高开发效率。支持代码生成、审查、错误诊断和智能对话。" />
        <meta name="twitter:image" content="/logo.png" />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
} 