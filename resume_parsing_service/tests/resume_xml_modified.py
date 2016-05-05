"""
The following is designed to set up XML trees that contain multiple variations of parsed results.
The goal is to not assign things the gT parsing library cannot extract from the Burning Glass results.
This is intended to cover situations like:
 * What happens when we parse an address with no city?
 * Can we parse a job experience with no 'job detail points' without crashing?
 * Do skills without a start and end month attribute get included in our list of results?
"""

CONTACT = """
<contact>
  <name>
   <givenname>
    BRUCE
   </givenname>
   <surname>
    PARKEY
   </surname>
  </name>
  Senior iOS Contract Developer
  <email>
   bparkey@sagamoreapps.com
  </email>
  <phone area="630">
   630-930-2756
  </phone>
  <address inferred-city="PORTLAND" inferred-country="USA" inferred-county="MULTNOMAH" inferred-phone-area-code="503" inferred-state="OR" lat="45.567589" lma="MT413890" lon="-122.642487" majorcity="PORTLAND" msa="38900: METROPOLITAN STATISTICAL AREA" state="OR">
    <street>1602 NE Junior St.</street>
    <city majorcity="portland">Portland</city>
    <state abbrev="OR">Oregon</state>
    <postalcode inferred-city="PORTLAND" inferred-country="USA" inferred-county="MULTNOMAH" inferred-phone-area-code="503" inferred-state="OR" lat="45.567589" lma="MT413890" lon="-122.642487" msa="38900: METROPOLITAN STATISTICAL AREA">97211</postalcode>
  </address>
</contact>
"""

PDF_13 = """
  <resdoc>
   <resume canonversion="2" dateversion="2" iso8601="2015-12-09" present="735943" xml:space="preserve">
    <contact>
     <name>
      <givenname>
       BRUCE
      </givenname>
      <surname>
       PARKEY
      </surname>
     </name>
     Senior iOS Contract Developer
     <email>
      bparkey@sagamoreapps.com
     </email>
     <phone area="630">
      630-930-2756
     </phone>
    </contact>
    <summary>
     CAREER SUMMARY
     <summary>
      I am a former CIO and for the last 4+ years have been developing iOS applications. An experienced
iOS developer, I have published 7 apps in the App Store and 1 app using Apple's Enterprise
Distribution Program.
     </summary>
     TECHNICAL EXPERTISE
     <summary>
      Expert in iOS design and development

   ·   Objective C, Cocoa Touch, Xcode 6 and iOS 8
   ·   Core Data, ARC, Memory Management, Storyboards and Interface Builder
   ·   iPhone, iPad and Universal Apps
   ·   JSON, Asynchronous and Synchronous Communications
   ·   MapKit and Location Services
   ·   App Store and Enterprise Program Distribution
   ·   4+ years experience in iOS design and development
   ·   Experience designing and developing complex applications
   ·   12 years managing developers in multiple development platforms
   ·   Learning Swift programming language
     </summary>
    </summary>
    <experience end="present" start="729757">
     PROFESSIONAL EXPERIENCE
     <job bgtocc="11-9021.00" end="present" id="1" inferred-naics="33" inferred-naics-jobtext="33" onet="11-9021.00|15-1199.04" onetrank="1" pos="1" span="8" start="733044">
      <employer clean="Sagamore Apps, Inc" consolidated="Sagamore Apps, Inc" invalid="false" priority="3">
       Sagamore Apps, Inc
      </employer>
      .,
      <address division-code="16974: METROPOLITAN DIVISION" inferred-city="DARIEN" inferred-country="USA" inferred-county="DUPAGE" inferred-phone-area-code="630" inferred-state="IL" lat="41.75" lma="DV171697|MT171698" lon="-87.98" majorcity="DARIEN" msa="16980: METROPOLITAN STATISTICAL AREA" state="IL">
       <city majorcity="darien">
        Darien
       </city>
       ,
       <state abbrev="IL">
        IL
       </state>
      </address>
      ,
      <daterange>
       <start days="733044" iso8601="2008-01-01">
        2008
       </start>
       -
       <end days="present" iso8601="2015-12-09">
        Present
       </end>
      </daterange>
      <title bgonetmodel-topic-onet="11-9021.00|15-1199.04" clean="Owner and Senior iOS" internship-flag="false" onet="11-9021.00|15-1199.04" onetrank="1">
       Owner and Senior iOS
      </title>
      <jobtype hours="fulltime" taxterm="contractor" type="temporary">
       Contract Developer
      </jobtype>
      <description>
       iPhone and iPad application design and development

   · Go! Team Go! Baseball Scorecard for iPad manages a baseball team's schedule, roster, scoring,
       and calculates complex statistics for batting, pitching and fielding. Syncs data with website and
       web app for displaying play by play scoring results. Easy to use but very complex application
       with storyboard, popovers, settings and asynchronous communication with server.
   ·   Survey for iPad enables Healthcare consultants to interview hospital employees and collect data
       for sync with server. Saves $500,000 annually in labor costs compared to prior method of
       manually compiling and editing reports. App sync with website for updating questions and
       response choices as well as posting responses to questions.
   ·   New Page Productions pHood Calculator for iPhone/iPad helps users make better food choices
       by calculating their pH balance based on the foods they eat. Graphic elements are used to
       display the results and guide the user.
   ·   New Page Productions Toxic Screening Test for iPhone/iPad helps users determine what
       products would help them meet their goals. Easy to use and integrates with website.
   ·   Advanse Ad Manager for iPhone trade show prototype allows users to update display ad content
       via their iPhone. Syncs with website.
          Bruce Parkey - Page 2 of 2
   · Prairie Architect Around Chicago for iPhone/iPad helps users find prairie style architecture.
       Utilizes MapKit, Location Services and Custom TableView Rows.
   · Movies Filmed in Chicago for iPhone/iPad helps users find filming locations for their favorite
       movies. Utilizes MapKit, Location Services and Custom TableView Rows.
   · Developed IT Governance processes for $2B manufacturer and distributer.
   · Developed IT strategic plan and software evaluation for event scheduling business.
      </description>
     </job>
     <job bgtocc="11-3021.00" end="732679" id="2" inferred-naics="523920" onet="11-3021.00|11-1011.00" onetrank="1" pos="2" sic="738999" sic2="73" span="4" start="731218">
      <employer city="MT . PROSPECT" clean="Rapid Solutions Group" consolidated="RAPID SOLUTIONS GROUP" invalid="false" name="RAPID SOLUTIONS GROUP" priority="2" referenced-naics="5418|5413" sic="738999" state="IL">
       Rapid Solutions Group
      </employer>
      (subsidiary of
      <employer city="MT . PROSPECT" clean="Janus Capital Group" consolidated="Janus Capital Group" inferred-naics="523920" invalid="false" name="JANUS CAPITAL GROUP INCORPORATED" priority="1" referenced-naics="5418|5413" sic="738917" state="IL" std="Janus Capital Group" ticker="JNS">
       Janus Capital Group
      </employer>
      ),
      <address division-code="16974: METROPOLITAN DIVISION" inferred-city="MOUNT PROSPECT" inferred-country="USA" inferred-county="COOK" inferred-phone-area-code="847" inferred-state="IL" lat="42.07" lma="DV171697|MT171698" lon="-87.93" majorcity="MOUNT PROSPECT" msa="16980: METROPOLITAN STATISTICAL AREA" state="IL">
       <city majorcity="mt . prospect">
        Mt. Prospect
       </city>
       ,
       <state abbrev="IL">
        IL
       </state>
      </address>
      ,
      <daterange>
       <start days="731218" iso8601="2003-01-01">
        2003
       </start>
       -
       <end days="732679" iso8601="2007-01-01">
        2007
       </end>
      </daterange>
      <title bgonetmodel-topic-onet="11-1011.00|11-9111.00" clean="Vice President and Chief Information Officer" internship-flag="false" onet="11-1011.00|11-9111.00" onetrank="1" std="Chief Information Officer">
       Vice President and Chief Information Officer
      </title>
      <description>
       Responsible for print production and document composition systems, PMO for delivery of client and
technology projects, software development, network services, data communications, data center and
digital prepress. Directed staff of 45. Provided executive sales support for strategic clients.

   · Implemented Critical Chain Project Management methodology achieving over 25% reduction of
       project duration and increase in project throughput.
   · Managed large-scale project to outsource high availability data center achieving world-class
       results for security, privacy, system availability and scalability including 99.99% uptime metrics.
   · Developed and implemented life-cycle project management processes including organization-
       wide cross-functional teams and removing silos for project team performance.
   · Managed $6M P&amp;L with responsibility for $3M of client revenue for IT projects and services,
       exceeding annual EBITDA goals by over $1M.
   · Established stand-alone network services during transition from former parent company (DST)
       to Janus Capital Group ownership including conversion from Lotus Notes to Outlook on
       schedule and budget.
      </description>
     </job>
     <job end="731218" id="3" onet="11-1021.00|11-3031.02" onetrank="1" pos="3" sic="733101" sic2="73" span="4" start="729757">
      <employer city="WILLOWBROOK" clean="AMS Direct, Inc" consolidated="AMS DIRECT" invalid="false" name="AMS DIRECT" priority="2" referenced-naics="5111|5418" sic="733101" state="IL">
       AMS Direct, Inc
      </employer>
      .,
      <address division-code="16974: METROPOLITAN DIVISION" inferred-city="WILLOWBROOK" inferred-country="USA" inferred-county="DUPAGE" inferred-phone-area-code="630" inferred-state="IL" lat="41.84" lma="DV171697|MT171698" lon="-87.95" majorcity="WILLOWBROOK" msa="16980: METROPOLITAN STATISTICAL AREA" state="IL">
       <city majorcity="willowbrook">
        Burr Ridge
       </city>
       ,
       <state abbrev="IL">
        IL
       </state>
      </address>
      ,
      <daterange>
       <start days="729757" iso8601="1999-01-01">
        1999
       </start>
       -
       <end days="731218" iso8601="2003-01-01">
        2003
       </end>
      </daterange>
      <title bgonetmodel-topic-onet="11-3031.02|11-9033.00" clean="Vice President" internship-flag="false" onet="11-3031.02|11-9033.00" onetrank="1">
       Vice President
      </title>
      Information Technology
      <description>
       Responsible for enterprise IT, project management, software development, web development, quality
assurance and network services. Directed staff of 15. Selected and managed outsource vendor
services including web hosting, network engineering and technical consulting. Managed additional
functional areas including product development, procurement and fulfillment operations.

   · Achieved significant turnaround of IT function in first year by restructuring staff, introducing
       structured work processes, upgrading vendors and stabilizing/improving technical infrastructure
       while reducing spending by $250,000
   ·   Implemented CoreMedia media management system improving EBITDA by over $1M annually
   ·   Developed consumer software product on time and budget, generating $6M+ in annual sales
   ·   Implemented efficiency and cost-reduction programs including consolidating multi-location
       computer operations, automating returns processing, procurement improvements and
       outsourcing fulfillment operations resulting in over $1M savings annually
   ·   Planned and managed seamless technology move into new corporate headquarters
      </description>
     </job>
    </experience>
    <education>
     EDUCATION AND TRAINING
     <school id="4">
      <degree level="16" name="Bachelor's">
       Bachelor of Science
      </degree>
      <major cipcode="52.1201" code="0404" std-major="MANAGEMENT INFORMATION SYSTEMS, GENERAL">
       Information Systems
      </major>
      ,
      <institution>
       Purdue University
      </institution>
     </school>
    </education>
    <professional>
     <description>
      Aligning IT with the Enterprise, American Management Association
Large-Scale Project Management
Critical Chain Project Management
4X4 Business Communication
Primer-Michaels Leadership
PMI Certification Training
     </description>
    </professional>
   </resume>
   <skillrollup version="1">
    <canonskill end="735943" experience="1" expidrefs="1" idrefs="1" lastused="2015" name="Application Design" posrefs="1" skill-cluster="IT: Programming, Development, and Engineering; Specialized Skills" start="733044">
     <variant>
      application design
     </variant>
    </canonskill>
    <canonskill name="Business Communications" skill-cluster="Common Skills: Communication and Coordination">
     <variant>
      Business Communication
     </variant>
    </canonskill>
    <canonskill end="735943" experience="1" expidrefs="1" idrefs="1" lastused="2015" name="Calculator" posrefs="1" skill-cluster="Specialized Skills" start="733044">
     <variant>
      Calculator
     </variant>
    </canonskill>
    <canonskill name="Cocoa" skill-cluster="IT: Programming, Development, and Engineering; Specialized Skills; Digital Media and Design: Tech Development and Design; Software and Programming Skills">
     <variant>
      Cocoa
     </variant>
    </canonskill>
    <canonskill end="731218" experience="1" expidrefs="3" idrefs="3" lastused="2003" name="Computer Skills" posrefs="3" skill-cluster="Common Skills" start="729757">
     <variant>
      computer operations
     </variant>
    </canonskill>
    <canonskill end="732679" experience="1" expidrefs="2" idrefs="2" lastused="2007" name="Data Communications" posrefs="2" skill-cluster="Specialized Skills" start="731218">
     <variant>
      data communications
     </variant>
    </canonskill>
    <canonskill end="735943" experience="1" expidrefs="1" idrefs="1" lastused="2015" name="Editing" posrefs="1" skill-cluster="Common Skills: Communication and Coordination" start="733044">
     <variant>
      editing
     </variant>
    </canonskill>
    <canonskill end="731218" experience="1" expidrefs="3" idrefs="3" lastused="2003" name="Internet Hosting" posrefs="3" skill-cluster="Digital Media and Design: Tech Development and Design; Specialized Skills" start="729757">
     <variant>
      web hosting
     </variant>
    </canonskill>
    <canonskill name="JSON" skill-cluster="IT: Programming, Development, and Engineering; Specialized Skills">
     <variant>
      JSON
     </variant>
    </canonskill>
    <canonskill end="732679" experience="1" expidrefs="2" idrefs="2" lastused="2007" name="Lotus Notes" posrefs="2" skill-cluster="Software and Programming Skills; Common Skills: Communication and Coordination" start="731218">
     <variant>
      Lotus Notes
     </variant>
    </canonskill>
    <canonskill end="731218" experience="1" expidrefs="3" idrefs="3" lastused="2003" name="Network Engineering" posrefs="3" skill-cluster="IT: Network Administration and Security; Specialized Skills" start="729757">
     <variant>
      network engineering
     </variant>
    </canonskill>
    <canonskill name="Objective C" skill-cluster="IT: Programming, Development, and Engineering; Specialized Skills; Digital Media and Design: Tech Development and Design; Software and Programming Skills">
     <variant>
      Objective C
     </variant>
    </canonskill>
    <canonskill end="732679" experience="1" expidrefs="2" idrefs="2" lastused="2007" name="Organizational Skills" posrefs="2" skill-cluster="Common Skills: Business Environment Skills" start="731218">
     <variant>
      organization
     </variant>
    </canonskill>
    <canonskill end="731218" experience="1" expidrefs="3" idrefs="3" lastused="2003" name="Outsourcing" posrefs="3" skill-cluster="HR: Staffing and Recruiting; Specialized Skills" start="729757">
     <variant>
      outsourcing
     </variant>
    </canonskill>
    <canonskill end="732679" experience="1" expidrefs="2" idrefs="2" lastused="2007" name="Pre - Press Production" posrefs="2" skill-cluster="Marketing: Public Relations; Specialized Skills" start="731218">
     <variant>
      prepress
     </variant>
    </canonskill>
    <canonskill end="732679" experience="1" expidrefs="2" idrefs="2" lastused="2007" name="Print Production" posrefs="2" skill-cluster="Specialized Skills" start="731218">
     <variant>
      print production
     </variant>
    </canonskill>
    <canonskill end="731218" experience="1" expidrefs="3" idrefs="3" lastused="2003" name="Processing Item Returns" posrefs="3" skill-cluster="Customer Service: Sales; Specialized Skills" start="729757">
     <variant>
      returns
     </variant>
    </canonskill>
    <canonskill end="731218" experience="1" expidrefs="3" idrefs="3" lastused="2003" name="Procurement" posrefs="3" skill-cluster="Specialized Skills; Supply Chain and Logistics: General" start="729757">
     <variant>
      procurement
     </variant>
    </canonskill>
    <canonskill end="731218" experience="1" expidrefs="3" idrefs="3" lastused="2003" name="Product Development" posrefs="3" skill-cluster="Product Design and Development; Specialized Skills" start="729757">
     <variant>
      product development
     </variant>
    </canonskill>
    <canonskill end="732679" experience="1" expidrefs="2,3" idrefs="2,3" lastused="2007" name="Project Management" posrefs="2,3" skill-cluster="Common Skills: Project and Process Flow Skills" start="729757">
     <variant>
      Project Management
     </variant>
     <variant>
      project management
     </variant>
    </canonskill>
    <canonskill end="732679" experience="1" expidrefs="2" idrefs="2" lastused="2007" name="Sales Support" posrefs="2" skill-cluster="Sales: General; Specialized Skills" start="731218">
     <variant>
      sales support
     </variant>
    </canonskill>
    <canonskill end="735943" experience="1" expidrefs="1" idrefs="1" lastused="2015" name="Scheduling" posrefs="1" skill-cluster="Neutral Skills; Specialized Skills" start="733044">
     <variant>
      scheduling
     </variant>
    </canonskill>
    <canonskill end="735943" experience="1" expidrefs="1" idrefs="1" lastused="2015" name="Screening" posrefs="1" skill-cluster="Specialized Skills" start="733044">
     <variant>
      Screening
     </variant>
    </canonskill>
    <canonskill end="731218" experience="1" expidrefs="3" idrefs="3" lastused="2003" name="Web Site Development" posrefs="3" skill-cluster="Digital Media and Design: Tech Development and Design; Specialized Skills" start="729757">
     <variant>
      web development
     </variant>
    </canonskill>
   </skillrollup>
   <dataelementsrollup version="5.5.18 TalentMine v3.2.5.3">
    <certification>
     PMI
    </certification>
    <canoncertification>
     <certification name="PROJECT MANAGEMENT CERTIFICATION (E.G. PMP)" type="Certification">
     </certification>
    </canoncertification>
   </dataelementsrollup>
  </resdoc>
"""