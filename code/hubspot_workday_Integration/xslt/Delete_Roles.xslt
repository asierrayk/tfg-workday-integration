<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:bsvc="urn:com.workday/bsvc">
   <xsl:for-each select="root">
   <soapenv:Header>
      <bsvc:Workday_Common_Header>
         <!--Optional:-->
         <bsvc:Include_Reference_Descriptors_In_Response>true</bsvc:Include_Reference_Descriptors_In_Response>
      </bsvc:Workday_Common_Header>
      <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
        <wsse:UsernameToken xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
            <wsse:Username><xsl:value-of select="user"/>@<xsl:value-of select="tenant"/></wsse:Username>
            <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText"><xsl:value-of select="password"/></wsse:Password>
        </wsse:UsernameToken>
      </wsse:Security>
   </soapenv:Header>
   <soapenv:Body>
      <bsvc:Assign_Roles_Request bsvc:version="v27.2">
         <!--Optional:-->
         <bsvc:Business_Process_Parameters>
            <!--Optional:-->
            <bsvc:Auto_Complete>true</bsvc:Auto_Complete>
            <!--Optional:-->
            <bsvc:Run_Now>true</bsvc:Run_Now>
            <!--Optional:-->
            <!--<bsvc:Comment_Data>-->
               <!--Optional:-->
               <!--<bsvc:Comment>?</bsvc:Comment>-->
               <!--Optional:-->
               <!--<bsvc:Worker_Reference bsvc:Descriptor="?">-->
                  <!--Zero or more repetitions:-->
                  <!--<bsvc:ID bsvc:type="?">?</bsvc:ID>-->
               <!--</bsvc:Worker_Reference>-->
            <!--</bsvc:Comment_Data>-->
            <!--Zero or more repetitions:-->
            <!--<bsvc:Business_Process_Attachment_Data>-->
               <!--<bsvc:File_Name>?</bsvc:File_Name>-->
               <!--Optional:-->
               <!--<bsvc:Event_Attachment_Description>?</bsvc:Event_Attachment_Description>-->
               <!--Optional:-->
               <!--<bsvc:Event_Attachment_Category_Reference bsvc:Descriptor="?">-->
                  <!--Zero or more repetitions:-->
                  <!--<bsvc:ID bsvc:type="?">?</bsvc:ID>-->
               <!--</bsvc:Event_Attachment_Category_Reference>-->
               <!--Optional:-->
               <!--<bsvc:File></bsvc:File>-->
               <!--Optional:-->
               <!--<bsvc:Content_Type>?</bsvc:Content_Type>-->
            <!--</bsvc:Business_Process_Attachment_Data>-->
         </bsvc:Business_Process_Parameters>
         <bsvc:Assign_Roles_Event_Data>
            <!--Optional:-->
            <!--<bsvc:Effective_Date>?</bsvc:Effective_Date>-->
            <!--Optional:-->
            <!--<bsvc:Effective_Timezone_Reference bsvc:Descriptor="?">-->
               <!--Zero or more repetitions:-->
               <!--<bsvc:ID bsvc:type="?">?</bsvc:ID>-->
            <!--</bsvc:Effective_Timezone_Reference>-->
            <bsvc:Event_Target_Assignee_Reference bsvc:Descriptor="?">
               <!--Zero or more repetitions:-->
               <bsvc:ID bsvc:type="Position_ID"><xsl:value-of select="position_id"/></bsvc:ID>
            </bsvc:Event_Target_Assignee_Reference>
            <!--Optional:-->
            <bsvc:Remove_All_Role_Assignments_for_Event_Target_Assignee>false</bsvc:Remove_All_Role_Assignments_for_Event_Target_Assignee>
            <!--Zero or more repetitions:-->
            <bsvc:Assign_Roles_Role_Assignment_Data>
               <bsvc:Role_Assigner_Reference bsvc:Descriptor="?">
                  <!--Zero or more repetitions:-->
                  <bsvc:ID bsvc:type="Project_ID"><xsl:value-of select="project_id"/></bsvc:ID>
               </bsvc:Role_Assigner_Reference>
               <bsvc:Assignable_Role_Reference bsvc:Descriptor="?">
                  <!--Zero or more repetitions:-->
                  <bsvc:ID bsvc:type="Organization_Role_ID"><xsl:value-of select="role"/></bsvc:ID>
               </bsvc:Assignable_Role_Reference>
               <!--Optional:-->
               <bsvc:Remove_Existing_Assignees_for_Assignable_Role_on_Role_Assigner>true</bsvc:Remove_Existing_Assignees_for_Assignable_Role_on_Role_Assigner>
               <!--Optional:-->
               <bsvc:Update_Later_Dated_Assignments>true</bsvc:Update_Later_Dated_Assignments>
               <!--Zero or more repetitions:-->
               <!--<bsvc:Assignees_to_Add_Reference bsvc:Descriptor="?">-->
                  <!--Zero or more repetitions:-->
                  <!--<bsvc:ID bsvc:type="Position_ID"></bsvc:ID>-->
               <!--</bsvc:Assignees_to_Add_Reference>-->
               <!--Zero or more repetitions:-->
               <!--<bsvc:Assignees_to_Remove_Reference bsvc:Descriptor="?">-->
                  <!--Zero or more repetitions:-->
                  <!--<bsvc:ID bsvc:type="?">?</bsvc:ID>-->
               <!--</bsvc:Assignees_to_Remove_Reference>-->
               <!--Optional:-->
               <!--<bsvc:Supervisory_Organization_Single_Assignment_Manager_Reference bsvc:Descriptor="?">-->
                  <!--Zero or more repetitions:-->
                  <!--<bsvc:ID bsvc:type="?">?</bsvc:ID>-->
               <!--</bsvc:Supervisory_Organization_Single_Assignment_Manager_Reference>-->
               <!--Optional:-->
               <!--<bsvc:Remove_Supervisory_Organization_Single_Assignment_Manager>?</bsvc:Remove_Supervisory_Organization_Single_Assignment_Manager>-->
            </bsvc:Assign_Roles_Role_Assignment_Data>
         </bsvc:Assign_Roles_Event_Data>
      </bsvc:Assign_Roles_Request>
   </soapenv:Body>
</xsl:for-each>
</soapenv:Envelope>
</xsl:template>
</xsl:stylesheet>