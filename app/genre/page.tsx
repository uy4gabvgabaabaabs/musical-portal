import type {Metadata} from "next";
import FilmExplorer from "../films/film-explorer";

export const metadata:Metadata={title:"ژانرهای فیلم | درگاه موزیکال",description:"مرور فیلم‌های موزیکال بر اساس ژانر"};

export default function GenrePage(){return <FilmExplorer genrePage/>}
