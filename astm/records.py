# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""Common ASTM records structure.


This module contains base ASTM records mappings with only defined common
required fields for most implementations. Others are marked as
:class:`~astm.mapping.NotUsedField` and should be defined explicitly for your
ASTM realisation.
"""


from datetime import datetime
from .mapping import (
    Record, ConstantField, DateTimeField, IntegerField, NotUsedField,
    TextField, RepeatedComponentField, Component

)

__all__ = ['HeaderRecord', 'PatientRecord', 'OrderRecord',
           'ResultRecord', 'CommentRecord', 'TerminatorRecord']

#: +-----+--------------+---------------------------------+-------------------+
#: |  #  | ASTM Field # | ASTM Name                       | Python alias      |
#: +=====+==============+=================================+===================+
#: |   1 |        7.1.1 |             ASTM Record Type ID |              type |
#: +-----+--------------+---------------------------------+-------------------+
#: |   2 |        7.1.2 |            Delimiter Definition |         delimeter |
#: +-----+--------------+---------------------------------+-------------------+
#: |   3 |        7.1.3 |              Message Control ID |        message_id |
#: +-----+--------------+---------------------------------+-------------------+
#: |   4 |        7.1.4 |                 Access Password |          password |
#: +-----+--------------+---------------------------------+-------------------+
#: |   5 |        7.1.5 |               Sender Name or ID |            sender |
#: +-----+--------------+---------------------------------+-------------------+
#: |   6 |        7.1.6 |           Sender Street Address |           address |
#: +-----+--------------+---------------------------------+-------------------+
#: |   7 |        7.1.7 |                  Reserved Field |          reserved |
#: +-----+--------------+---------------------------------+-------------------+
#: |   8 |        7.1.8 |         Sender Telephone Number |             phone |
#: +-----+--------------+---------------------------------+-------------------+
#: |   9 |        7.1.9 |       Characteristics of Sender |              caps |
#: +-----+--------------+---------------------------------+-------------------+
#: |  10 |       7.1.10 |                     Receiver ID |          receiver |
#: +-----+--------------+---------------------------------+-------------------+
#: |  11 |       7.1.11 |                        Comments |          comments |
#: +-----+--------------+---------------------------------+-------------------+
#: |  12 |       7.1.12 |                   Processing ID |     processing_id |
#: +-----+--------------+---------------------------------+-------------------+
#: |  13 |       7.1.13 |                  Version Number |           version |
#: +-----+--------------+---------------------------------+-------------------+
#: |  14 |       7.1.14 |            Date/Time of Message |         timestamp |
#: +-----+--------------+---------------------------------+-------------------+
#:
HeaderRecord = Record.build(
    ConstantField(name='type', default='H'),
    RepeatedComponentField(Component.build(
        ConstantField(name='_', default=''),
        TextField(name='__')
    ), name='delimeter', default=[[], ['', '&']]),
    # ^^^ workaround to define field:
    # ConstantField(name='delimeter', default='\^&'),
    NotUsedField(name='message_id'),
    NotUsedField(name='password'),
    NotUsedField(name='sender'),
    NotUsedField(name='address'),
    NotUsedField(name='reserved'),
    NotUsedField(name='phone'),
    NotUsedField(name='caps'),
    NotUsedField(name='receiver'),
    NotUsedField(name='comments'),
    ConstantField(name='processing_id', default='P'),
    NotUsedField(name='version'),
    DateTimeField(name='timestamp', default=datetime.now, required=True),
)


#: +-----+--------------+---------------------------------+-------------------+
#: |  #  | ASTM Field # | ASTM Name                       | Python alias      |
#: +=====+==============+=================================+===================+
#: |   1 |        8.1.1 |                  Record Type ID |              type |
#: +-----+--------------+---------------------------------+-------------------+
#: |   2 |        8.1.2 |                 Sequence Number |               seq |
#: +-----+--------------+---------------------------------+-------------------+
#: |   3 |        8.1.3 |    Practice Assigned Patient ID |       practice_id |
#: +-----+--------------+---------------------------------+-------------------+
#: |   4 |        8.1.4 |  Laboratory Assigned Patient ID |     laboratory_id |
#: +-----+--------------+---------------------------------+-------------------+
#: |   5 |        8.1.5 |                      Patient ID |                id |
#: +-----+--------------+---------------------------------+-------------------+
#: |   6 |        8.1.6 |                    Patient Name |              name |
#: +-----+--------------+---------------------------------+-------------------+
#: |   7 |        8.1.7 |            Mother’s Maiden Name |       maiden_name |
#: +-----+--------------+---------------------------------+-------------------+
#: |   8 |        8.1.8 |                       Birthdate |         birthdate |
#: +-----+--------------+---------------------------------+-------------------+
#: |   9 |        8.1.9 |                     Patient Sex |               sex |
#: +-----+--------------+---------------------------------+-------------------+
#: |  10 |       8.1.10 |      Patient Race-Ethnic Origin |              race |
#: +-----+--------------+---------------------------------+-------------------+
#: |  11 |       8.1.11 |                 Patient Address |           address |
#: +-----+--------------+---------------------------------+-------------------+
#: |  12 |       8.1.12 |                  Reserved Field |          reserved |
#: +-----+--------------+---------------------------------+-------------------+
#: |  13 |       8.1.13 |        Patient Telephone Number |             phone |
#: +-----+--------------+---------------------------------+-------------------+
#: |  14 |       8.1.14 |          Attending Physician ID |      physician_id |
#: +-----+--------------+---------------------------------+-------------------+
#: |  15 |       8.1.15 |                Special Field #1 |         special_1 |
#: +-----+--------------+---------------------------------+-------------------+
#: |  16 |       8.1.16 |                Special Field #2 |         special_2 |
#: +-----+--------------+---------------------------------+-------------------+
#: |  17 |       8.1.17 |                  Patient Height |            height |
#: +-----+--------------+---------------------------------+-------------------+
#: |  18 |       8.1.18 |                  Patient Weight |            weight |
#: +-----+--------------+---------------------------------+-------------------+
#: |  19 |       8.1.19 |       Patient’s Known Diagnosis |         diagnosis |
#: +-----+--------------+---------------------------------+-------------------+
#: |  20 |       8.1.20 |     Patient’s Active Medication |        medication |
#: +-----+--------------+---------------------------------+-------------------+
#: |  21 |       8.1.21 |                  Patient’s Diet |              diet |
#: +-----+--------------+---------------------------------+-------------------+
#: |  22 |       8.1.22 |            Practice Field No. 1 |  practice_field_1 |
#: +-----+--------------+---------------------------------+-------------------+
#: |  23 |       8.1.23 |            Practice Field No. 2 |  practice_field_2 |
#: +-----+--------------+---------------------------------+-------------------+
#: |  24 |       8.1.24 |       Admission/Discharge Dates |    admission_date |
#: +-----+--------------+---------------------------------+-------------------+
#: |  25 |       8.1.25 |                Admission Status |  admission_status |
#: +-----+--------------+---------------------------------+-------------------+
#: |  26 |       8.1.26 |                        Location |          location |
#: +-----+--------------+---------------------------------+-------------------+
#:
PatientRecord = Record.build(
    ConstantField(name='type', default='P'),
    IntegerField(name='seq', default=1, required=True),
    NotUsedField(name='practice_id'),
    NotUsedField(name='laboratory_id'),
    NotUsedField(name='id'),
    NotUsedField(name='name'),
    NotUsedField(name='maiden_name'),
    NotUsedField(name='birthdate'),
    NotUsedField(name='sex'),
    NotUsedField(name='race'),
    NotUsedField(name='address'),
    NotUsedField(name='reserved'),
    NotUsedField(name='phone'),
    NotUsedField(name='physician_id'),
    NotUsedField(name='special_1'),
    NotUsedField(name='special_2'),
    NotUsedField(name='height'),
    NotUsedField(name='weight'),
    NotUsedField(name='diagnosis'),
    NotUsedField(name='medication'),
    NotUsedField(name='diet'),
    NotUsedField(name='practice_field_1'),
    NotUsedField(name='practice_field_2'),
    NotUsedField(name='admission_date'),
    NotUsedField(name='admission_status'),
    NotUsedField(name='location'),
    NotUsedField(name='diagnostic_code_nature'),
    NotUsedField(name='diagnostic_code'),
    NotUsedField(name='religion'),
    NotUsedField(name='martial_status'),
    NotUsedField(name='isolation_status'),
    NotUsedField(name='language'),
    NotUsedField(name='hospital_service'),
    NotUsedField(name='hospital_institution'),
    NotUsedField(name='dosage_category'),
)


#: +-----+--------------+--------------------------------+--------------------+
#: |  #  | ASTM Field # | ASTM Name                      | Python alias       |
#: +=====+==============+================================+====================+
#: |   1 |        9.4.1 |                 Record Type ID |               type |
#: +-----+--------------+--------------------------------+--------------------+
#: |   2 |        9.4.2 |                Sequence Number |                seq |
#: +-----+--------------+--------------------------------+--------------------+
#: |   3 |        9.4.3 |                    Specimen ID |          sample_id |
#: +-----+--------------+--------------------------------+--------------------+
#: |   4 |        9.4.4 |         Instrument Specimen ID |         instrument |
#: +-----+--------------+--------------------------------+--------------------+
#: |   5 |        9.4.5 |              Universal Test ID |               test |
#: +-----+--------------+--------------------------------+--------------------+
#: |   6 |        9.4.6 |                       Priority |           priority |
#: +-----+--------------+--------------------------------+--------------------+
#: |   7 |        9.4.7 |    Requested/Ordered Date/Time |         created_at |
#: +-----+--------------+--------------------------------+--------------------+
#: |   8 |        9.4.8 |  Specimen Collection Date/Time |         sampled_at |
#: +-----+--------------+--------------------------------+--------------------+
#: |   9 |        9.4.9 |            Collection End Time |       collected_at |
#: +-----+--------------+--------------------------------+--------------------+
#: |  10 |       9.4.10 |              Collection Volume |             volume |
#: +-----+--------------+--------------------------------+--------------------+
#: |  11 |       9.4.11 |                   Collector ID |          collector |
#: +-----+--------------+--------------------------------+--------------------+
#: |  12 |       9.4.12 |                    Action Code |        action_code |
#: +-----+--------------+--------------------------------+--------------------+
#: |  13 |       9.4.13 |                    Danger Code |        danger_code |
#: +-----+--------------+--------------------------------+--------------------+
#: |  14 |       9.4.14 |           Relevant Information |      clinical_info |
#: +-----+--------------+--------------------------------+--------------------+
#: |  15 |       9.4.15 |    Date/Time Specimen Received |       delivered_at |
#: +-----+--------------+--------------------------------+--------------------+
#: |  16 |       9.4.16 |            Specimen Descriptor |        biomaterial |
#: +-----+--------------+--------------------------------+--------------------+
#: |  17 |       9.4.17 |             Ordering Physician |          physician |
#: +-----+--------------+--------------------------------+--------------------+
#: |  18 |       9.4.18 |        Physician’s Telephone # |    physician_phone |
#: +-----+--------------+--------------------------------+--------------------+
#: |  19 |       9.4.19 |               User Field No. 1 |       user_field_1 |
#: +-----+--------------+--------------------------------+--------------------+
#: |  20 |       9.4.20 |               User Field No. 2 |       user_field_2 |
#: +-----+--------------+--------------------------------+--------------------+
#: |  21 |       9.4.21 |         Laboratory Field No. 1 | laboratory_field_1 |
#: +-----+--------------+--------------------------------+--------------------+
#: |  22 |       9.4.22 |         Laboratory Field No. 2 | laboratory_field_2 |
#: +-----+--------------+--------------------------------+--------------------+
#: |  23 |       9.4.23 |             Date/Time Reported |        modified_at |
#: +-----+--------------+--------------------------------+--------------------+
#: |  24 |       9.4.24 |              Instrument Charge |  instrument_charge |
#: +-----+--------------+--------------------------------+--------------------+
#: |  25 |       9.4.25 |          Instrument Section ID | instrument_section |
#: +-----+--------------+--------------------------------+--------------------+
#: |  26 |       9.4.26 |                    Report Type |        report_type |
#: +-----+--------------+--------------------------------+--------------------+
#:
OrderRecord = Record.build(
    ConstantField(name='type', default='O'),
    IntegerField(name='seq', default=1, required=True),
    NotUsedField(name='sample_id'),
    NotUsedField(name='instrument'),
    NotUsedField(name='test'),
    NotUsedField(name='priority'),
    NotUsedField(name='created_at'),
    NotUsedField(name='sampled_at'),
    NotUsedField(name='collected_at'),
    NotUsedField(name='volume'),
    NotUsedField(name='collector'),
    NotUsedField(name='action_code'),
    NotUsedField(name='danger_code'),
    NotUsedField(name='clinical_info'),
    NotUsedField(name='delivered_at'),
    NotUsedField(name='biomaterial'),
    NotUsedField(name='physician'),
    NotUsedField(name='physician_phone'),
    NotUsedField(name='user_field_1'),
    NotUsedField(name='user_field_2'),
    NotUsedField(name='laboratory_field_1'),
    NotUsedField(name='laboratory_field_2'),
    NotUsedField(name='modified_at'),
    NotUsedField(name='instrument_charge'),
    NotUsedField(name='instrument_section'),
    NotUsedField(name='report_type'),
    NotUsedField(name='reserved'),
    NotUsedField(name='location_ward'),
    NotUsedField(name='infection_flag'),
    NotUsedField(name='specimen_service'),
    NotUsedField(name='laboratory')
)

#: +-----+--------------+--------------------------------+--------------------+
#: |  #  | ASTM Field # | ASTM Name                      | Python alias       |
#: +=====+==============+================================+====================+
#: |   1 |       10.1.1 |                 Record Type ID |               type |
#: +-----+--------------+--------------------------------+--------------------+
#: |   2 |       10.1.2 |                Sequence Number |                seq |
#: +-----+--------------+--------------------------------+--------------------+
#: |   3 |       10.1.3 |              Universal Test ID |               test |
#: +-----+--------------+--------------------------------+--------------------+
#: |   4 |       10.1.4 |      Data or Measurement Value |              value |
#: +-----+--------------+--------------------------------+--------------------+
#: |   5 |       10.1.5 |                          Units |              units |
#: +-----+--------------+--------------------------------+--------------------+
#: |   6 |       10.1.6 |               Reference Ranges |         references |
#: +-----+--------------+--------------------------------+--------------------+
#: |   7 |       10.1.7 |          Result Abnormal Flags |      abnormal_flag |
#: +-----+--------------+--------------------------------+--------------------+
#: |   8 |       10.1.8 |     Nature of Abnormal Testing | abnormality_nature |
#: +-----+--------------+--------------------------------+--------------------+
#: |   9 |       10.1.9 |                 Results Status |             status |
#: +-----+--------------+--------------------------------+--------------------+
#: |  10 |      10.1.10 | Date of Change in Instrument   |   norms_changed_at |
#: |     |              | Normative Values               |                    |
#: +-----+--------------+--------------------------------+--------------------+
#: |  11 |      10.1.11 |        Operator Identification |           operator |
#: +-----+--------------+--------------------------------+--------------------+
#: |  12 |      10.1.12 |         Date/Time Test Started |         started_at |
#: +-----+--------------+--------------------------------+--------------------+
#: |  13 |      10.1.13 |        Date/Time Test Complete |       completed_at |
#: +-----+--------------+--------------------------------+--------------------+
#: |  14 |      10.1.14 |      Instrument Identification |         instrument |
#: +-----+--------------+--------------------------------+--------------------+
#:
ResultRecord = Record.build(
    ConstantField(name='type', default='R'),
    IntegerField(name='seq', default=1, required=True),
    NotUsedField(name='test'),
    NotUsedField(name='value'),
    NotUsedField(name='units'),
    NotUsedField(name='references'),
    NotUsedField(name='abnormal_flag'),
    NotUsedField(name='abnormality_nature'),
    NotUsedField(name='status'),
    NotUsedField(name='norms_changed_at'),
    NotUsedField(name='operator'),
    NotUsedField(name='started_at'),
    NotUsedField(name='completed_at'),
    NotUsedField(name='instrument'),
)

#: +-----+--------------+---------------------------------+-------------------+
#: |  #  | ASTM Field # | ASTM Name                       | Python alias      |
#: +=====+==============+=================================+===================+
#: |   1 |       11.1.1 |                  Record Type ID |              type |
#: +-----+--------------+---------------------------------+-------------------+
#: |   2 |       11.1.2 |                 Sequence Number |               seq |
#: +-----+--------------+---------------------------------+-------------------+
#: |   3 |       11.1.3 |                  Comment Source |            source |
#: +-----+--------------+---------------------------------+-------------------+
#: |   4 |       11.1.4 |                    Comment Text |              data |
#: +-----+--------------+---------------------------------+-------------------+
#: |   5 |       11.1.5 |                    Comment Type |             ctype |
#: +-----+--------------+---------------------------------+-------------------+
#:
CommentRecord = Record.build(
    ConstantField(name='type', default='C'),
    IntegerField(name='seq', default=1, required=True),
    NotUsedField(name='source'),
    NotUsedField(name='data'),
    NotUsedField(name='ctype')
)

#: +-----+--------------+---------------------------------+-------------------+
#: |  #  | ASTM Field # | ASTM Name                       | Python alias      |
#: +=====+==============+=================================+===================+
#: |   1 |       13.1.1 |                  Record Type ID |              type |
#: +-----+--------------+---------------------------------+-------------------+
#: |   2 |       13.1.2 |                 Sequence Number |               seq |
#: +-----+--------------+---------------------------------+-------------------+
#: |   3 |       13.1.3 |                Termination code |              code |
#: +-----+--------------+---------------------------------+-------------------+
#:
TerminatorRecord = Record.build(
    ConstantField(name='type', default='L'),
    ConstantField(name='seq', default=1, field=IntegerField()),
    ConstantField(name='code', default='N')
)

#: +-----+--------------+---------------------------------+-------------------+
#: |  #  | ASTM Field # | ASTM Name                       | Python alias      |
#: +=====+==============+=================================+===================+
#: |   1 |       14.1.1 |                  Record Type ID |              type |
#: +-----+--------------+---------------------------------+-------------------+
#: |   2 |       14.1.2 |                 Sequence Number |               seq |
#: +-----+--------------+---------------------------------+-------------------+
#: |   3 |       14.1.3 |               Analytical Method |            method |
#: +-----+--------------+---------------------------------+-------------------+
#: |   4 |       14.1.4 |                 Instrumentation |        instrument |
#: +-----+--------------+---------------------------------+-------------------+
#: |   5 |       14.1.5 |                        Reagents |          reagents |
#: +-----+--------------+---------------------------------+-------------------+
#: |   6 |       14.1.6 |                Units of Measure |             units |
#: +-----+--------------+---------------------------------+-------------------+
#: |   7 |       14.1.7 |                 Quality Control |                qc |
#: +-----+--------------+---------------------------------+-------------------+
#: |   8 |       14.1.8 |             Specimen Descriptor |       biomaterial |
#: +-----+--------------+---------------------------------+-------------------+
#: |   9 |       14.1.9 |                  Reserved Field |          reserved |
#: +-----+--------------+---------------------------------+-------------------+
#: |  10 |      14.1.10 |                       Container |         container |
#: +-----+--------------+---------------------------------+-------------------+
#: |  11 |      14.1.11 |                     Specimen ID |         sample_id |
#: +-----+--------------+---------------------------------+-------------------+
#: |  12 |      14.1.12 |                         Analyte |           analyte |
#: +-----+--------------+---------------------------------+-------------------+
#: |  13 |      14.1.13 |                          Result |            result |
#: +-----+--------------+---------------------------------+-------------------+
#: |  14 |      14.1.14 |                    Result Units |      result_units |
#: +-----+--------------+---------------------------------+-------------------+
#: |  15 |      14.1.15 |        Collection Date and Time |        sampled_at |
#: +-----+--------------+---------------------------------+-------------------+
#: |  16 |      14.1.16 |            Result Date and Time |      completed_at |
#: +-----+--------------+---------------------------------+-------------------+
#: |  17 |      14.1.17 |  Analytical Preprocessing Steps |      preanalytics |
#: +-----+--------------+---------------------------------+-------------------+
#: |  18 |      14.1.18 |               Patient Diagnosis |         diagnosis |
#: +-----+--------------+---------------------------------+-------------------+
#: |  19 |      14.1.19 |               Patient Birthdate |         birthdate |
#: +-----+--------------+---------------------------------+-------------------+
#: |  20 |      14.1.20 |                     Patient Sex |               sex |
#: +-----+--------------+---------------------------------+-------------------+
#: |  21 |      14.1.21 |                    Patient Race |              race |
#: +-----+--------------+---------------------------------+-------------------+
#:
ScientificRecord = Record.build(
    ConstantField(name='type', default='S'),
    IntegerField(name='seq', default=1, required=True),
    NotUsedField(name='method'),
    NotUsedField(name='instrument'),
    NotUsedField(name='reagents'),
    NotUsedField(name='units'),
    NotUsedField(name='qc'),
    NotUsedField(name='biomaterial'),
    NotUsedField(name='reserved'),
    NotUsedField(name='container'),
    NotUsedField(name='sample_id'),
    NotUsedField(name='analyte'),
    NotUsedField(name='result'),
    NotUsedField(name='result_units'),
    NotUsedField(name='sampled_at'),
    NotUsedField(name='completed_at'),
    NotUsedField(name='preanalytics'),
    NotUsedField(name='diagnosis'),
    NotUsedField(name='birthdate'),
    NotUsedField(name='sex'),
    NotUsedField(name='race'),
)

#: +-----+--------------+---------------------------------+-------------------+
#: |  #  | ASTM Field # | ASTM Name                       | Python alias      |
#: +=====+==============+=================================+===================+
#: |   1 |       15.1.1 |                  Record Type ID |              type |
#: +-----+--------------+---------------------------------+-------------------+
#: |   2 |       15.1.2 |                 Sequence Number |               seq |
#: +-----+--------------+---------------------------------+-------------------+
#:
#: .. note::
#:   This record, which is similar to the comment record, may be used to send
#:   complex structures where use of the existing record types would not be
#:   appropriate. The fields within this record type are defined by the
#:   manufacturer.
#:
ManufacturerInfoRecord = Record.build(
    ConstantField(name='type', default='M'),
    IntegerField(name='seq', default=1, required=True),
)
