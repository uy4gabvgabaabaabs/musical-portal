import type {Metadata} from "next";
import FilmExplorer from "../films/film-explorer";
export const metadata:Metadata={title:"فیلم‌ها بر اساس سبک موسیقایی | درگاه موزیکال",description:"مرور فیلم‌های موزیکال بر اساس سبک موسیقایی"};
export default function StylePage(){return <FilmExplorer stylePage/>}
