"use client";

type Props={prompt:string;className?:string};

export default function GPTButton({prompt,className=""}:Props){
  function openGPT(){
    navigator.clipboard?.writeText(prompt).catch(()=>undefined);
    window.open(`https://chatgpt.com/?q=${encodeURIComponent(prompt)}`,"_blank","noopener,noreferrer");
  }
  return <button className={`gpt-button ${className}`.trim()} onClick={openGPT} title="پرسش آماده می‌شود و در ChatGPT باز خواهد شد">GPT</button>;
}
