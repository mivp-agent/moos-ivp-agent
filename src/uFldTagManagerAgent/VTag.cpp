/*****************************************************************/
/*    NAME: Michael Benjamin                                     */
/*    ORGN: Dept of Mechanical Eng / CSAIL, MIT Cambridge MA     */
/*    FILE: VTag.cpp                                             */
/*    DATE: Sep 21st, 2015                                       */
/*                                                               */
/* This program is free software; you can redistribute it and/or */
/* modify it under the terms of the GNU General Public License   */
/* as published by the Free Software Foundation; either version  */
/* 2 of the License, or (at your option) any later version.      */
/*                                                               */
/* This program is distributed in the hope that it will be       */
/* useful, but WITHOUT ANY WARRANTY; without even the implied    */
/* warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR       */
/* PURPOSE. See the GNU General Public License for more details. */
/*                                                               */
/* You should have received a copy of the GNU General Public     */
/* License along with this program; if not, write to the Free    */
/* Software Foundation, Inc., 59 Temple Place - Suite 330,       */
/* Boston, MA 02111-1307, USA.                                   */
/*****************************************************************/

#include "VTag.h"
#include "MBUtils.h"

using namespace std;

//------------------------------------------------------------
// Constructor

VTag::VTag()
{
  m_x      = 0;
  m_y      = 0;
  m_range  = -1;
  m_event  = 0;

  m_time_posted = 0;

  m_x_set = false;
  m_y_set = false;
}


//------------------------------------------------------------
// Constructor

VTag::VTag(string vname, double x, double y, double time_posted)
{
  m_vname  = vname;
  m_x      = x;
  m_y      = y;
  m_range  = -1;
  m_event  = 0;

  m_time_posted = time_posted;

  m_x_set = true;
  m_y_set = true;
  m_time_set  = true;
  m_event_set = false;
}

//------------------------------------------------------------
// Procedure: valid()

bool VTag::valid() const
{
  if(!m_x_set || !m_y_set || !m_time_set || !m_event_set)
    return(false);
  if(m_time_posted <= 0)
    return(false);
  if(m_vname == "")
    return(false);
  if(m_vteam == "")
    return(false);
  return(true);
}


//------------------------------------------------------------
// Procedure: str()

string VTag::str() const
{
  string spec = "vname=" + m_vname;
  spec += ",vteam=" + m_vteam;
  spec += ",x=" + doubleToString(m_x,2);
  spec += ",y=" + doubleToString(m_y,2);
  spec += ",time_posted=" + doubleToString(m_time_posted,2);
  spec += ",event=" + uintToString(m_event);
  spec += ",range=" + doubleToString(m_range,2);

  return(spec);
}
