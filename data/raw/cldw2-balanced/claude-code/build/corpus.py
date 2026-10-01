# -*- coding: utf-8 -*-
IA = "https://archive.org/download/{0}/{0}_djvu.txt"
PG = "https://www.gutenberg.org/cache/epub/{0}/pg{0}.txt"

# (title, author, gender, genre, year, repo, key, reason)
E = []
def ia(t,a,g,ge,y,k,r): E.append((t,a,g,ge,y,"Internet Archive",IA.format(k),r))
def pg(t,a,g,ge,y,k,r): E.append((t,a,g,ge,y,"Project Gutenberg",PG.format(k),r))

# --- Early modern chorography & natural history ---
ia("The Second Part, or a Continuance of Poly-Olbion, from the Eighteenth Song","Michael Drayton","M","Chorographical poem",1622,"draytonpolyolbion2ndpart",
   "The Thirtieth Song is a verse chorography of Westmorland and Cumberland, personifying Winandermere, Derwentwater and the Lakeland fells")
ia("Britannia: or, a Chorographical Description of the Flourishing Kingdoms of England, Scotland and Ireland (Gough's edition, volume 3)","William Camden","M","Chorography",1806,"b33544827_0003",
   "Volume three contains the full Cumberland and Westmorland chorographies, describing Winandermere, Derwentwater, Kendal and the mountain country")
ia("An Essay towards a Natural History of Westmorland and Cumberland","Thomas Robinson","M","Natural history",1709,"b30517035",
   "The earliest sustained natural history of the Lake counties, covering the fells, minerals, springs and lakes of Westmorland and Cumberland")
ia("A Tour thro' the Whole Island of Great Britain, Divided into Circuits or Journeys (volume containing Letter X)","Daniel Defoe","M","Travel",1742,"gri_33125010870554",
   "Contains Defoe's self-contained circuit through Westmorland and Cumberland, with Kendal, Cockermouth, Whitehaven and the 'unhospitable terror' of the fells")
ia("A Miscellany of Poems, consisting of Original Poems, Translations, Pastorals in the Cumberland Dialect","Josiah Relph","M","Poetry",1747,"miscellanyofpoem00relp",
   "The first collection of Cumberland dialect pastorals, written from the northern edge of the Lake District around Sebergham and Penrith")

# --- Eighteenth-century tours, guides and antiquarianism ---
ia("An Excursion to the Lakes in Westmoreland and Cumberland, August 1773","William Hutchinson","M","Travel",1774,"excursiontolakes00hutc",
   "One of the earliest published Lake District tours, describing Windermere, Coniston, Derwentwater and Ullswater day by day")
ia("The Antiquities of Furness; or, an Account of the Royal Abbey of St Mary in the Vale of Nightshade","Thomas West","M","Antiquarian",1774,"isbn_9781140976547",
   "Facsimile of the 1774 first edition; the standard antiquarian history of Furness, covering Furness Abbey, Cartmel, Coniston and the southern Lake District")
ia("A Guide to the Lakes, Dedicated to the Lovers of Landscape Studies","Thomas West","M","Guide",1778,"guidetolakesdedi00westiala",
   "The first true Lake District guidebook, setting out the celebrated 'stations' from which tourists should view each lake")
ia("The History and Antiquities of the Counties of Westmorland and Cumberland, volume 1","Joseph Nicolson","M","County history",1777,"historyantiquiti01nico",
   "Compiled with Richard Burn; the foundational parish-by-parish county history of Westmorland and Cumberland, covering the whole Lake District")
ia("Observations, Relative Chiefly to Picturesque Beauty, Made in the Year 1772, on Several Parts of England, Particularly the Mountains and Lakes of Cumberland and Westmoreland","William Gilpin","M","Travel, picturesque",1788,"gri_33125011693567",
   "The founding text of picturesque Lake District travel, devoted wholly to the mountains and lakes of Cumberland and Westmoreland")
ia("A Survey of the Lakes of Cumberland, Westmorland, and Lancashire","James Clarke","M","Topography",1789,"bim_eighteenth-century_a-survey-of-the-lakes-of_clarke-james_1789",
   "A Penrith land surveyor's detailed survey of every Lake District lake with local history, customs and anecdote")
ia("The History of the County of Cumberland, and Some Places Adjacent, volume 1","William Hutchinson","M","County history",1794,"historyofcountyo01hutc",
   "Comprehensive county history covering Keswick, Borrowdale, Derwentwater and the Cumberland fell parishes")
pg("A Journey Made in the Summer of 1794 through Holland and the Western Frontier of Germany, with a Return down the Rhine: to which are Added Observations during a Tour to the Lakes of Lancashire, Westmoreland, and Cumberland, volume 2","Ann Radcliffe","F","Travel",1795,"64218",
   "The second volume contains Radcliffe's substantial self-contained tour of the Lakes of Lancashire, Westmoreland and Cumberland")
ia("A Fortnight's Ramble to the Lakes in Westmorland, Lancashire, and Cumberland","Joseph Budworth (Joseph Palmer)","M","Travel",1795,"cu31924103708032",
   "A pedestrian tour of the Lakes including the first published account of climbing Helvellyn and Great Gable")
ia("The Lakers: A Comic Opera in Three Acts","James Plumptre","M","Drama, satire",1798,"cu31924104104223",
   "A satire on Lake District tourism, set among picturesque tourists at Keswick, Borrowdale and Skiddaw")
ia("A Companion and Useful Guide to the Beauties of Scotland, to the Lakes of Westmoreland, Cumberland, and Lancashire","Sarah Murray","F","Guide",1799,"acompanionandus00murrgoog",
   "A pioneering woman traveller's practical guide with an extended section on the Lakes of Westmoreland, Cumberland and Lancashire")
pg("Through England on a Side Saddle in the Time of William and Mary","Celia Fiennes","F","Diary, travel",1888,
   "72156","Her 1698 northern journey includes a self-contained passage through Kendal, Windermere, Ullswater and Cumberland, the earliest woman's account of the region")
ia("The Works of Thomas Gray in Prose and Verse, volume 3 (containing the Journal in the Lakes, 1769)","Thomas Gray","M","Journal",1775,"worksofthomasgra03gray_0",
   "Contains Gray's Journal in the Lakes, the 1769 day-by-day account of Keswick, Borrowdale and Skiddaw that shaped Lake tourism; text from the 1884 collected Works")

# --- Romantic period ---
ia("A Descriptive Tour, and Guide to the Lakes, Caves, Mountains, and Other Natural Curiosities in Cumberland, Westmoreland, Lancashire","John Housman","M","Guide",1808,"descriptivetour00hous",
   "A Cumberland-born writer's systematic descriptive guide to the lakes, caves and mountains of the three Lake counties")
pg("Letters from England, by Don Manuel Alvarez Espriella, volume 2","Robert Southey","M","Travel, letters",1807,"61506",
   "Contains Southey's extended fictionalised letters on the Lakes, with Keswick, Lodore, Skiddaw and Ambleside described at length")
ia("The Minstrel of the North; or, Cumbrian Legends: Being a Poetical Miscellany","John Stagg","M","Poetry",1810,"minstrelofnortho00stag",
   "Verse legends of Cumberland by the blind Wigton poet, drawing on Eskdale, Keswick and Cumbrian folklore")
ia("The Excursion, being a Portion of The Recluse: A Poem","William Wordsworth","M","Poetry",1814,"excursionpoem00worduoft",
   "Wordsworth's long philosophical poem set entirely in Lake District valleys, churchyards and fells around Grasmere and Langdale")
ia("The Bridal of Triermain; and Miscellaneous Poems","Walter Scott","M","Narrative poetry",1813,"bridaloftriermai00scot",
   "Text from a later collected printing of a verse romance set at Triermain, Threlkeld and the Vale of St John in Cumberland, with Lakeland landscape throughout")
ia("Fragments, in Prose and Verse, by Miss Elizabeth Smith, with some Account of her Life and Character","Elizabeth Smith","F","Memoir, letters",1818,"fragmentsinprose00smitiala",
   "Letters and journal fragments written during the author's residence at Patterdale and Coniston, with detailed Lakeland description")
ia("The Tourist's New Guide, containing a Description of the Lakes, Mountains, and Scenery in Cumberland, Westmorland, and Lancashire","William Green","M","Guide",1819,"touristsnewguid00greegoog",
   "A resident Ambleside artist's two-volume descriptive guide to the whole Lake District")
ia("Tours to the British Mountains, with the Descriptive Poems of Lowther and Emont Vale","Thomas Wilkinson","M","Travel, poetry",1824,"cu31924104096015",
   "A Quaker Penrith writer's mountain tours centred on Helvellyn, Langdale, Borrowdale and the Cumberland fells")
ia("A Concise Description of the English Lakes and Adjacent Mountains","Jonathan Otley","M","Guide, geology",1827,"concisedescripti00otle",
   "The Keswick guide-writer's compact description of the lakes with the first sound account of Lake District geology")
ia("A Guide through the District of the Lakes in the North of England, with a Description of the Scenery, &c. for the Use of Tourists and Residents","William Wordsworth","M","Guide",1835,"guidethroughdist00word",
   "Wordsworth's own prose guide to the Lake District, the classic statement of its landscape, society and conservation")
pg("Journals of Dorothy Wordsworth, volume 1","Dorothy Wordsworth","F","Diary",1897,"42856",
   "The Grasmere journal, a day-by-day record of life, weather and walking in the Lake District between 1800 and 1803")
pg("Recollections of a Tour Made in Scotland, A.D. 1803","Dorothy Wordsworth","F","Travel diary",1874,"28880",
   "The tour begins and ends in the Lake District, with sustained description of Keswick, Grasmere and the passage out of Cumberland")
ia("Anima Poetae: from the Unpublished Note-books of Samuel Taylor Coleridge","Samuel Taylor Coleridge","M","Notebooks",1895,"animapoetaefromu01cole",
   "Notebook entries from Coleridge's Greta Hall years, including his celebrated Scafell and Borrowdale fell-walking observations")
pg("Letters of John Keats to His Family and Friends","John Keats","M","Letters",1891,"35698",
   "Contains the run of letters from Keats's 1818 northern walking tour describing Windermere, Ambleside, Helvellyn and Skiddaw")

# --- Victorian guides, tourism, topography ---
ia("Ballads in the Cumberland Dialect, with Notes Descriptive of the Manners of the Peasantry","Robert Anderson","M","Poetry, dialect",1840,"balladsincumberl00andeuoft",
   "The classic Cumberland dialect ballads, recording fell-country speech, fairs, weddings and customs")
ia("The Poetical Works of Miss Susanna Blamire, 'The Muse of Cumberland'","Susanna Blamire","F","Poetry",1842,"cu31924102775743",
   "Collected poems and Cumberland dialect songs by the 'Muse of Cumberland', rooted in the Caldbeck fells and Carlisle plain")
ia("A Complete Guide to the Lakes, comprising Minute Directions for the Tourist, with Mr Wordsworth's Description of the Scenery of the Country and Three Letters upon the Geology of the Lake District","John Hudson","M","Guide, geology",1842,"completeguidetol00hudsiala",
   "Edited with Adam Sedgwick; combines a Kendal tourist guide, Wordsworth's Description and Sedgwick's three letters on Lake District geology")
pg("Recreations of Christopher North, volume 2","John Wilson","M","Essays",1842,"19938",
   "Contains Wilson's Lake District essays and rambles around Windermere, Rydal and Elleray where he lived")
ia("The Scenery and Poetry of the English Lakes: A Summer Ramble","Charles Mackay","M","Travel",1846,"cu31924103707893",
   "A summer ramble through the Lake District interwoven with the poetry the region generated")
pg("Homes and Haunts of the Most Eminent British Poets, volume 2","William Howitt","M","Literary topography",1847,"45887",
   "Contains extended chapters on Wordsworth at Rydal and Grasmere and on Southey and Coleridge at Keswick")
pg("The Old Man; or, Ravings and Ramblings round Conistone","Alexander Craig Gibson","M","Topography",1849,"56462",
   "Rambles round Coniston Old Man by a Lakeland doctor, with fell-walking, mining and local character sketches")
pg("Half a Life-Time Ago","Elizabeth Gaskell","F","Short fiction",1855,"2547",
   "A tale set wholly among the Westmorland fells and farms above Coniston and Langdale")
ia("A Complete Guide to the English Lakes","Harriet Martineau","F","Guide",1855,"completeguidetoe1855mart",
   "The standard guide by a resident of Ambleside, combining topography with Lake District society and economy")
ia("The Northmen in Cumberland and Westmoreland","Robert Ferguson","M","Antiquarian",1856,"northmenincumber00fergrich",
   "An antiquarian study of Norse settlement and place-names throughout the Lake District valleys")
ia("On the Drifts of the West and South Borders of the Lake District, and on the Three Great Granite Dispersions","Daniel Mackintosh","M","Geological survey",1871,"ondriftsofwestso00mack",
   "A field survey of glacial drifts and erratic dispersion around the western and southern margins of the Lake District")
ia("Cumberland and Westmorland, Ancient and Modern: The People, Dialect, Superstitions and Customs","Jeremiah Sullivan","M","Topography, folklife",1857,"cu31924028028532",
   "A Kendal writer's account of the people, dialect, superstitions and customs of the Lake counties")
pg("The Lazy Tour of Two Idle Apprentices","Charles Dickens","M","Travel narrative",1857,"888",
   "Written with Wilkie Collins; opens with a sustained comic account of the ascent of Carrock Fell in Cumberland in driving rain")
ia("The History and Topography of the Counties of Cumberland and Westmorland","William Whellan","M","County history",1860,"historytopograp00whel",
   "An exhaustive directory-history of every parish in Cumberland and Westmorland, including all the Lake District valleys")
ia("The Annals of Kendal: being a Historical and Descriptive Account of Kendal and the Neighbourhood","Cornelius Nicholson","M","Local history",1861,"annalsofkendalbe00nich",
   "History of Kendal and its Westmorland hinterland, the traditional gateway town to the Lake District")
ia("Recollections of the Lakes and the Lake Poets: Coleridge, Wordsworth, and Southey","Thomas De Quincey","M","Memoir",1862,"cu31924075217236",
   "De Quincey's memoir of his years at Dove Cottage and of Lakeland life among the Lake Poets")
ia("The Lake Country","Eliza Lynn Linton","F","Topography",1864,"lakecountry00lintiala",
   "A Cumberland-born writer's valley-by-valley account of Lake District landscape, people and traditions")
ia("Lizzie Lorton of Greyrigg: A Novel","Eliza Lynn Linton","F","Novel",1866,"lizzielortongre02lintgoog",
   "A novel of Cumberland fell and coastal village life, drawing on the author's Crosthwaite childhood near Keswick")
ia("The Worthies of Cumberland","Henry Lonsdale","M","Biography",1867,"cu31924104094937",
   "Collective biography of notable Cumbrians, with lives rooted in Keswick, Cockermouth and the Lakeland fells")
pg("The Folk-Speech of Cumberland and Some Districts Adjacent","Alexander Craig Gibson","M","Dialect, folklore",1869,"62370",
   "Dialect stories and rhymes recording the speech and folklife of Cumberland and the Lake District valleys")
ia("Annales Caermoelenses, or Annals of Cartmel","James Stockdale","M","Local history",1872,"annalescaermoel00stocgoog",
   "A detailed history of Cartmel and its priory in the southern Lake District, with Windermere and Furness material")
pg("Lays and Legends of the English Lake Country, with Copious Notes","John Pagen White","M","Poetry, folklore",1873,"48207",
   "A verse collection dedicated entirely to Lake District legends, places and traditions, with topographical notes")
pg("Lady Anna","Anthony Trollope","M","Novel",1874,"31274",
   "A substantial part of the novel is set in and around Keswick and the Cumberland lakes")
ia("Autobiography of Mrs Fletcher, with Letters and Other Family Memorials","Eliza Fletcher","F","Autobiography",1875,"autobiographyofm00flet",
   "The memoir of a long resident of Lancrigg, Grasmere, recording Lake District society, Wordsworth's circle and daily life")
ia("Cumbriana; or, Fragments of Cumbrian Life","William Dickinson","M","Folklife",1876,"cumbrianaorfragm00dick",
   "A West Cumberland farmer's record of Lakeland customs, sports, farming and dialect")
ia("The Geology of the Northern Part of the English Lake District (Memoirs of the Geological Survey, Quarter Sheet 101 S.E.)","James Clifton Ward","M","Geological survey",1876,"cu31924004550459",
   "The official Geological Survey memoir for the Skiddaw, Derwentwater and Borrowdale country")
ia("Harriet Martineau's Autobiography, volume 2","Harriet Martineau","F","Autobiography",1877,"harrietmartinea02martgoog",
   "Records her years at The Knoll, Ambleside, with extended accounts of Lake District neighbours and social life")
ia("Memoir and Letters of Sara Coleridge, volume 2","Sara Coleridge","F","Letters, memoir",1873,"memoirletters02cole",
   "Letters and reminiscences of her Greta Hall childhood at Keswick and of the Wordsworths at Rydal and Grasmere")
ia("Tourists' Guide to the English Lake District","Henry Irwin Jenkinson","M","Guide",1879,"touristsguideto00jenkgoog",
   "A detailed late-Victorian walking and touring guide to the whole Lake District")
ia("The Thorough Guide to the English Lake District","Mountford John Byrde Baddeley","M","Guide",1880,"thoroughguideto00baddgoog",
   "The most authoritative late-Victorian route guide to Lake District fells, passes and valleys")
ia("A Flora of the English Lake District","John Gilbert Baker","M","Natural history",1885,"floraofenglishla00bake",
   "The first systematic flora of the Lake District, mapping plant distribution across its fells and lakes")
pg("The Shadow of a Crime: A Cumbrian Romance","Hall Caine","M","Novel",1885,"14262",
   "A historical novel set in Borrowdale and the Newlands fells above Derwentwater")
pg("Robert Elsmere","Mary Augusta Ward","F","Novel",1888,"8737",
   "Opens with an extended Westmorland sequence in 'Long Whindale', a thinly disguised Lake District valley near Ullswater")
ia("A History of Cumberland","Richard Saul Ferguson","M","County history",1890,"historyofcumberl00fergiala",
   "A scholarly county history of Cumberland covering the Lake District fells, valleys and market towns")
ia("A Vertebrate Fauna of Lakeland, including Cumberland and Westmorland with Lancashire North of the Sands","Hugh Alexander Macpherson","M","Natural history",1892,"vertebratefaunao00macp",
   "The standard Victorian faunal survey of Lakeland, recording birds and mammals fell by fell and lake by lake")
pg("Tales and Legends of the English Lakes","Wilson Armistead","M","Folklore",1891,"42359",
   "A collection of legends and traditions attached to named Lake District lakes, fells and villages")
ia("Literary Associations of the English Lakes, volume 2","Hardwicke Drummond Rawnsley","M","Literary topography",1894,"literaryassociat02rawn",
   "A Keswick vicar's survey of the writers associated with each part of the Lake District")
pg("Climbing in the British Isles, volume 1: England","Walter Parry Haskett Smith","M","Mountaineering",1894,"37993",
   "The first British rock-climbing guide, whose largest section catalogues Lake District crags and gullies")
pg("Thorstein of the Mere: A Saga of the Northmen in Lakeland","William Gershom Collingwood","M","Novel",1895,"79129",
   "A historical novel of Norse settlement set on Coniston Water and the Furness fells")
pg("The Book of Coniston","William Gershom Collingwood","M","Local history",1897,"43968",
   "A history and description of Coniston, Torver and the surrounding Lake District fells")
pg("Helbeck of Bannisdale, volume 1","Mary Augusta Ward","F","Novel",1898,"9441",
   "Set at a Westmorland manor in the Lake District fell country, with landscape integral to the novel")
pg("Rock-Climbing in the English Lake District","Owen Glynne Jones","M","Mountaineering",1897,"56043",
   "Text of the posthumous third edition (1900) of the foundational Lake District climbing guide, describing routes on Scafell, Pillar, Gable and Great End")
pg("Lakeland Words: A Collection of Dialect Words and Phrases as Used in Cumberland and Westmorland","Bryham Kirkby","M","Dialect",1898,"58200",
   "A glossary and dialect sketches recording the everyday speech of Lake District farms and villages")
pg("Bygone Cumberland and Westmorland","Daniel Scott","M","Antiquarian",1899,"37891",
   "Antiquarian essays on the history, customs and legends of the Lake counties")
ia("Life and Nature at the English Lakes","Hardwicke Drummond Rawnsley","M","Natural history, essays",1899,"lifenatureatengl00rawniala",
   "Essays on Lake District birds, weather, shepherds and fell life by a resident Keswick clergyman")
ia("Praeterita: Outlines of Scenes and Thoughts Perhaps Worthy of Memory in My Past Life","John Ruskin","M","Autobiography",1889,"cu31924057667333",
   "Text from the 1899 issue; includes sustained passages on Ruskin's Keswick and Derwentwater childhood and his later life at Brantwood on Coniston Water")
pg("Hortus Inclusus: Messages from the Wood to the Garden","John Ruskin","M","Letters",1887,"22230",
   "Letters written from Brantwood to the Beever sisters at Coniston, closely observing Lake District weather and landscape")
pg("The Half-Brothers","Elizabeth Gaskell","F","Short fiction",1859,"2532",
   "A tale set entirely on the Cumberland fells, whose climax is a fatal snowstorm on the high fell above the family farm")
