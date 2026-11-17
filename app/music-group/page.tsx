import type {Metadata} from "next";
import MusicGroupProfile from "./music-group-profile";
import "../music-groups/music-groups.css";

export const metadata:Metadata={title:"پروندهٔ گروه موسیقی | درگاه موزیکال",description:"فیلم‌ها و مستندهای مرتبط با یک گروه موسیقی"};
export default function MusicGroupPage(){return <MusicGroupProfile/>}
