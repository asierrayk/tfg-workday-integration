<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:bsvc="urn:com.workday/bsvc">
   <xsl:for-each select="root">
   <soapenv:Header>
      <bsvc:Workday_Common_Header>
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
      <xsl:for-each select="project">
      <bsvc:Submit_Project_Request bsvc:Add_Only="true" bsvc:version="v27.2">
         <bsvc:Project_Data>
            <bsvc:Locked_in_Workday>false</bsvc:Locked_in_Workday>

            <xsl:if test="external_project_reference">
            <bsvc:External_Project_Reference_Name><xsl:value-of select="external_project_reference"/></bsvc:External_Project_Reference_Name>
            </xsl:if>

            <xsl:if test="hierarchy">
            <bsvc:Project_Hierarchy_Reference bsvc:Descriptor="hierarchy">
               <bsvc:ID bsvc:type="Project_Hierarchy_ID"><xsl:value-of select="hierarchy"/></bsvc:ID>
            </bsvc:Project_Hierarchy_Reference>
            </xsl:if>

             <xsl:if test="optional_hierarchy">
            <bsvc:Optional_Project_Hierarchy_Reference bsvc:Descriptor="?">
                <bsvc:ID bsvc:type="Project_Hierarchy_ID"><xsl:value-of select="optional_hierarchy"/></bsvc:ID>
            </bsvc:Optional_Project_Hierarchy_Reference>
            </xsl:if>


            <bsvc:Project_Name><xsl:value-of select="name"/></bsvc:Project_Name>
            <bsvc:Worktag_Only>false</bsvc:Worktag_Only>
            <bsvc:Inactive>false</bsvc:Inactive>

            <xsl:if test="status">
            <bsvc:Project_Status_Reference bsvc:Descriptor="status">
               <bsvc:ID bsvc:type="Project_Status_ID"><xsl:value-of select="status"/></bsvc:ID>
            </bsvc:Project_Status_Reference>
            </xsl:if>

            <bsvc:Include_Project_ID_in_Name>false</bsvc:Include_Project_ID_in_Name>
            <bsvc:Start_Date><xsl:value-of select="start_date"/></bsvc:Start_Date>

            <xsl:if test="currency">
            <bsvc:Currency_Reference bsvc:Descriptor="currency">
               <bsvc:ID bsvc:type="Currency_ID"><xsl:value-of select="currency"/></bsvc:ID>
            </bsvc:Currency_Reference>
            </xsl:if>

            <bsvc:Billable>true</bsvc:Billable>
            <bsvc:Capital>false</bsvc:Capital>
            <bsvc:Description><xsl:value-of select="description"/></bsvc:Description>
            <bsvc:Overall_Percent_Complete>0</bsvc:Overall_Percent_Complete>

            <xsl:if test="company">
            <bsvc:Company_Reference bsvc:Descriptor="company">
               <bsvc:ID bsvc:type="Company_Reference_ID"><xsl:value-of select="company"/></bsvc:ID>
            </bsvc:Company_Reference>
            </xsl:if>

            <xsl:if test="customer">
            <bsvc:Customer_Reference bsvc:Descriptor="customer">
               <bsvc:ID bsvc:type="Customer_ID"><xsl:value-of select="customer"/></bsvc:ID>
            </bsvc:Customer_Reference>
            </xsl:if>

             <xsl:if test="custom_org">
            <bsvc:Worktags_Data>
               <bsvc:Related_Worktags_by_Type_Data>
                  <bsvc:Worktag_Type_Reference bsvc:Descriptor="?">
                     <bsvc:ID bsvc:type="Accounting_Worktag_Type_ID">CUSTOM_ORGANIZATION_01</bsvc:ID>
                  </bsvc:Worktag_Type_Reference>
                  <bsvc:Required_On_Transaction>true</bsvc:Required_On_Transaction>
                  <bsvc:Required_On_Transaction_For_Validation>true</bsvc:Required_On_Transaction_For_Validation>
                  <bsvc:Default_Worktag_Data bsvc:Delete_Default_Value="false">
                     <bsvc:Default_Worktag_Reference bsvc:Descriptor="?">
                        <bsvc:ID bsvc:type="Custom_Organization_Reference_ID"><xsl:value-of select="custom_org"/></bsvc:ID>
                     </bsvc:Default_Worktag_Reference>
                  </bsvc:Default_Worktag_Data>
               </bsvc:Related_Worktags_by_Type_Data>
            </bsvc:Worktags_Data>
             </xsl:if>

         </bsvc:Project_Data>
      </bsvc:Submit_Project_Request>
      </xsl:for-each>
   </soapenv:Body>
   </xsl:for-each>
</soapenv:Envelope>
</xsl:template>
</xsl:stylesheet>