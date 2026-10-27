import React,{useState} from 'react';
import {Sun,Moon} from 'lucide-react';
import './ThemeControl.css';

let initial='dark';
try{if(localStorage.getItem('bridge-theme')==='light')initial='light'}catch{}
document.documentElement.dataset.theme=initial;
export default function ThemeControl(){
 const [theme,setTheme]=useState(initial);
 function change(value){setTheme(value);document.documentElement.dataset.theme=value;try{localStorage.setItem('bridge-theme',value)}catch{}}
 return <div className="theme-control-bar"><span>Appearance</span><div role="group" aria-label="Color theme"><button type="button" aria-pressed={theme==='light'} onClick={()=>change('light')}><Sun size={15} aria-hidden="true"/>Light</button><button type="button" aria-pressed={theme==='dark'} onClick={()=>change('dark')}><Moon size={15} aria-hidden="true"/>Dark</button></div></div>;
}
