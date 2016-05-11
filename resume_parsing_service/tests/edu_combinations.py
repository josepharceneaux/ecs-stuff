B_A_S_E = """
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
"""


school = """
<education>
 EDUCATION AND TRAINING
</education>
"""


degree = """
<education>
 EDUCATION AND TRAINING
 <school id="4">
  <major cipcode="52.1201" code="0404" std-major="MANAGEMENT INFORMATION SYSTEMS, GENERAL">
   Information Systems
  </major>
  ,
  <institution>
   Purdue University
  </institution>
 </school>
</education>
"""


major = """
<education>
 EDUCATION AND TRAINING
 <school id="4">
  <degree level="16" name="Bachelor's">
   Bachelor of Science
  </degree>
  ,
  <institution>
   Purdue University
  </institution>
 </school>
</education>
"""


institution = """
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
 </school>
</education>
"""


school_degree = """
<education>
 EDUCATION AND TRAINING
</education>
"""


school_major = """
<education>
 EDUCATION AND TRAINING
</education>
"""


school_institution = """
<education>
 EDUCATION AND TRAINING
</education>
"""


degree_major = """
<education>
 EDUCATION AND TRAINING
 <school id="4">
  ,
  <institution>
   Purdue University
  </institution>
 </school>
</education>
"""


degree_institution = """
<education>
 EDUCATION AND TRAINING
 <school id="4">
  <major cipcode="52.1201" code="0404" std-major="MANAGEMENT INFORMATION SYSTEMS, GENERAL">
   Information Systems
  </major>
  ,
 </school>
</education>
"""


major_institution = """
<education>
 EDUCATION AND TRAINING
 <school id="4">
  <degree level="16" name="Bachelor's">
   Bachelor of Science
  </degree>
  ,
 </school>
</education>
"""


school_degree_major = """
<education>
 EDUCATION AND TRAINING
</education>
"""


school_degree_institution = """
<education>
 EDUCATION AND TRAINING
</education>
"""


school_major_institution = """
<education>
 EDUCATION AND TRAINING
</education>
"""


degree_major_institution = """
<education>
 EDUCATION AND TRAINING
 <school id="4">
  ,
 </school>
</education>
"""


school_degree_major_institution = """
<education>
 EDUCATION AND TRAINING
</education>
"""


