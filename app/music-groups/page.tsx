import type {Metadata} from "next";
import MusicGroupsDirectory from "./music-groups-directory";
import "./music-groups.css";

export const metadata:Metadata={
  title:"گروه‌های موسیقی و فیلم‌ها | درگاه موزیکال",
  description:"فهرست گروه‌های موسیقی و پیوند آن‌ها با فیلم‌ها و مستندهای درگاه موزیکال"
};

export default function MusicGroupsPage(){return <MusicGroupsDirectory/>}
